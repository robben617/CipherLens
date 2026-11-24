import asyncio
import hashlib
import json
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from models.schemas import AiAskRequest, ModelTestRequest
from services import agent_tools, llm_service, web_search
from services.ai_service import (
    is_small_talk,
    small_talk_blocks,
    ai_cache_key,
    build_local_blocks,
    context_fingerprint,
    get_cached,
    iter_ai_events,
    normalize_question,
    put_cached,
    quotes_values,
    sanitize_context,
)

logger = logging.getLogger("cipherlens.ai")
router = APIRouter(prefix="/api/ai", tags=["AI 问答"])

LOCAL_DEADLINE_SECONDS = 20.0


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/ask",
    responses={400: {"description": "invalid request"}},
)
def ask_ai(payload: AiAskRequest, request: Request):
    async def event_stream():
        page = payload.page
        clean, missing, ignored = sanitize_context(page, payload.context)
        normalized = normalize_question(payload.question)
        fingerprint = context_fingerprint(page, clean)
        key = ai_cache_key(page, fingerprint, normalized)
        quoted = quotes_values(page, clean)
        common = {
            "page": page,
            "source": "local",
            "quotes_values": quoted,
            "conversation_id": payload.conversation_id,
            "model": "local",
            "context_valid": len(missing) == 0,
            "context_missing": missing,
            "context_ignored": ignored,
            "structured": True,
        }

        if is_small_talk(normalized):
            yield sse("meta", {**common, "cache": False})
            for block in small_talk_blocks(page, clean):
                yield sse("block", block)
            yield sse("done", {"finish": "stop", "degraded": False})
            return

        web_results = None
        if payload.web_search:
            yield sse("search_start", {"query": normalized})
            try:
                found = await web_search.search(normalized)
                web_results = found["results"]
                yield sse(
                    "search_result",
                    {
                        "ok": True,
                        "count": len(web_results),
                        "sources": [
                            {"title": item["title"], "url": item["url"], "domain": item["domain"]}
                            for item in web_results
                        ],
                    },
                )
            except web_search.SearchUnavailable as error:
                yield sse(
                    "search_result",
                    {"ok": False, "code": error.code, "message": error.message},
                )

        wants_agent = payload.llm is None and (
            agent_tools.detect_tool_call(normalized, None, 0) is not None
            or any(hint in normalized for hint in agent_tools.PRACTICE_HINTS)
        )
        cached = None if (wants_agent or payload.web_search) else get_cached(key)
        llm_degraded = False

        if wants_agent:
            yield sse("meta", {**common, "cache": False})
            content_emitted = False
            try:
                async for event, data in llm_service.stream_agent_page_answer(
                    page,
                    clean,
                    normalized,
                    None,
                    web_results=web_results,
                    tool_input=payload.tool_input,
                ):
                    if event == "audit":
                        continue
                    if event in ("tool_start", "tool_result", "tool_end", "block", "token"):
                        if event in ("block", "token"):
                            content_emitted = True
                        yield sse(event, data)
                if content_emitted:
                    yield sse("done", {"finish": "stop", "degraded": False})
                    return
            except llm_service.LLMUnavailable:
                pass

        if payload.llm is not None:
            display = payload.llm.display_name or payload.llm.model
            yield sse("meta", {**common, "source": "llm", "model": display, "cache": False})
            emitted = 0
            try:
                async for event, data in llm_service.stream_agent_page_answer(
                    page,
                    clean,
                    normalized,
                    payload.llm,
                    web_results=web_results,
                    tool_input=payload.tool_input,
                ):
                    if await request.is_disconnected():
                        logger.info("ai ask cancelled page=%s", page)
                        return
                    if event == "audit":
                        continue
                    if event in ("tool_start", "tool_result", "tool_end", "block", "token"):
                        if event in ("block", "token"):
                            emitted += 1
                        yield sse(event, data)
                if emitted == 0:
                    raise llm_service.LLMUnavailable(
                        "llm_empty", "模型没有返回内容", retryable=False
                    )
                logger.info("ai ask page=%s source=llm qlen=%s", page, len(normalized))
                yield sse("done", {"finish": "stop", "degraded": False})
                return
            except llm_service.LLMUnavailable as error:
                if emitted > 0:
                    # 已经吐了内容：保留已生成部分，让前端标记「不完整」
                    logger.warning(
                        "ai degraded page=%s detail=%s partial=true", page, error.code
                    )
                    yield sse(
                        "error",
                        {
                            "code": "llm_unavailable",
                            "message": error.message,
                            "retryable": bool(error.retryable),
                            "partial": True,
                        },
                    )
                    return
                logger.warning(
                    "ai degraded page=%s detail=%s partial=false", page, error.code
                )
                llm_degraded = True
                # 一字未出：改回本地讲解，重新声明来源，前端据此显示「本地」
                yield sse(
                    "meta",
                    {**common, "source": "local", "model": None, "cache": False, "degraded": True},
                )

        if cached is not None:
            yield sse("meta", {**common, "cache": True})
            for block in cached:
                yield sse("block", block)
            yield sse("done", {"finish": "stop", "degraded": llm_degraded})
            return

        yield sse("meta", {**common, "cache": False})

        deadline = time.monotonic() + LOCAL_DEADLINE_SECONDS
        try:
            blocks = build_local_blocks(page, clean, normalized)
            for event, data in iter_ai_events(page, clean, normalized):
                if await request.is_disconnected():
                    logger.info("ai ask cancelled page=%s", page)
                    return
                if time.monotonic() >= deadline:
                    yield sse("done", {"finish": "timeout", "degraded": True})
                    return
                yield sse(event, data)
                await asyncio.sleep(0)
            put_cached(key, blocks)
            logger.info(
                "ai ask page=%s source=local cache=false context_valid=%s missing=%s qlen=%s qhash=%s",
                page,
                len(missing) == 0,
                ",".join(missing),
                len(normalized),
                hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8],
            )
            yield sse("done", {"finish": "stop", "degraded": llm_degraded})
        except Exception:
            logger.exception("ai ask internal_error page=%s", page)
            yield sse(
                "error",
                {
                    "code": "internal_error",
                    "message": "讲解生成失败，请重试",
                    "retryable": True,
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.post("/model-test")
async def model_test(payload: ModelTestRequest):
    """连通性测试：真实请求一次模型，服务端不保存任何配置。"""
    try:
        latency = await llm_service.probe(
            payload.base_url, payload.api_key, payload.model
        )
    except llm_service.LLMUnavailable as error:
        return {"ok": False, "code": error.code, "message": error.message}
    return {"ok": True, "latency_ms": latency}