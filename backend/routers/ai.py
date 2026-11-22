import asyncio
import hashlib
import json
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from models.schemas import AiAskRequest
from services.ai_service import (
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

        cached = get_cached(key)
        if cached is not None:
            yield sse("meta", {**common, "cache": True})
            for block in cached:
                yield sse("block", block)
            yield sse("done", {"finish": "stop", "degraded": False})
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
            yield sse("done", {"finish": "stop", "degraded": False})
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