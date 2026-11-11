import asyncio
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from models.schemas import ErrorResponse, TutorRequest
from services import llm_service, tutor_log
from services.trace_store import get_trace
from services.tutor_service import (
    build_local_blocks,
    cache_key,
    get_cached,
    iter_block_events,
    put_cached,
    sse,
    step_label,
)

logger = logging.getLogger("cipherlens.tutor")

router = APIRouter(prefix="/api/tutor", tags=["AI 辅导"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# 每帧之间的间隔。原来恒为 30ms 且内容固定，看着像加载条；
# 现在帧数随正文长度变，间隔略缩，四块讲完约 2 秒。
FRAME_DELAY = 0.025

# 本地模板是纯内存拼装，20 秒还没讲完一定是卡住了；
# 模型这条路要给「首字 20 秒 + 重试 30 秒」留出余量。
LOCAL_DEADLINE_S = 20.0
LLM_DEADLINE_S = 45.0


class _ClientGone(Exception):
    """客户端断开。用异常跳出多层生成器，比逐层 return 干净。"""


def _meta(payload, step, label, cached, source, model):
    return {
        "trace_id": payload.trace_id,
        "step_index": payload.step_index,
        "step_label": label,
        "quotes_values": True,
        "source": source,
        "model": model,
        "structured": True,
        "round": step["round"],
        "op": step["op"],
        "question": payload.question,
        "cache": cached,
    }


async def _event_stream(request, payload):
    trace = get_trace(payload.trace_id)
    if trace is None:
        yield sse("error", {"code": "trace_not_found", "message": "trace_id 不存在或已过期"})
        return

    if payload.step_index >= trace["step_count"]:
        yield sse(
            "error",
            {"code": "step_out_of_range", "message": "step_index 超出当前 trace 的步数"},
        )
        return

    step = trace["steps"][payload.step_index]
    label = step_label(step, trace.get("direction", "encrypt"))
    key = cache_key(payload.trace_id, payload.step_index, payload.question)
    cached = get_cached(key)
    started = time.perf_counter()

    status = llm_service.public_status()
    use_llm = status["enabled"]
    source = "llm" if use_llm else "local"
    degraded = False
    fabricated = 0
    frames = 0
    timed_out = False
    failure = None

    logger.info(
        "tutor ask trace_id=%s step=%s cache=%s source=%s",
        payload.trace_id,
        payload.step_index,
        bool(cached),
        source,
    )

    if cached is not None:
        yield sse("meta", _meta(payload, step, cached["step_label"], True, "local", None))
        # 命中缓存不走逐字：缓存的意义就是立刻拿到，再慢慢打一遍反而像没命中。
        for block in cached["blocks"]:
            yield sse("block", block)
        yield sse(
            "done",
            {"finish": "stop", "tokens": len(cached["blocks"]), "elapsed_ms": 0, "degraded": False},
        )
        tutor_log.record(
            payload.trace_id,
            payload.step_index,
            payload.question,
            source="local",
            model=None,
            latency_ms=0,
            tokens=len(cached["blocks"]),
        )
        return

    yield sse(
        "meta",
        _meta(payload, step, label, False, source, status["model"] if use_llm else None),
    )

    async def local_frames():
        """本地模板的逐字流。LLM 失败时也用它顶上来，所以抽成生成器。"""
        nonlocal frames
        for event, data in iter_block_events(trace, payload.step_index, payload.question):
            if await request.is_disconnected():
                raise _ClientGone()
            yield sse(event, data)
            if event == "token":
                frames += 1
                await asyncio.sleep(FRAME_DELAY)

    deadline = time.monotonic() + (LLM_DEADLINE_S if use_llm else LOCAL_DEADLINE_S)

    try:
        if not use_llm:
            async for frame in local_frames():
                yield frame
        else:
            try:
                async for event, data in llm_service.stream_answer(
                    trace, payload.step_index, payload.question
                ):
                    if await request.is_disconnected():
                        raise _ClientGone()

                    if event == "audit":
                        # 内部记账帧：不上前端
                        outside = data.get("hex_outside") or []
                        fabricated = len(outside)
                        if outside:
                            logger.warning(
                                "llm invented hex trace_id=%s step=%s values=%s",
                                payload.trace_id,
                                payload.step_index,
                                [f"0x{value:02X}" for value in outside],
                            )
                        continue

                    if time.monotonic() >= deadline:
                        timed_out = True
                        break

                    yield sse(event, data)
                    if event == "token":
                        frames += 1
            except llm_service.LLMUnavailable as error:
                # 降级是设计的一部分，不是异常路径：现场网络断了也得有东西看
                degraded = True
                if error.audit:
                    fabricated = len(error.audit.get("hex_outside") or [])
                if not error.partial:
                    source = "local"
                    async for frame in local_frames():
                        yield frame
                failure = {
                    "code": "llm_unavailable",
                    "message": error.message,
                    "detail": error.code,
                    "retryable": bool(error.retryable),
                    "partial": bool(error.partial),
                }
                logger.warning(
                    "tutor degraded trace_id=%s step=%s detail=%s partial=%s",
                    payload.trace_id,
                    payload.step_index,
                    error.code,
                    error.partial,
                )
    except _ClientGone:
        logger.info("tutor cancelled trace_id=%s step=%s", payload.trace_id, payload.step_index)
        return
    except asyncio.CancelledError:
        logger.info("tutor cancelled trace_id=%s step=%s", payload.trace_id, payload.step_index)
        raise

    elapsed = int((time.perf_counter() - started) * 1000)

    if source == "local":
        # 只有本地模板进缓存。模型每次答的都不一样，缓存住反而会让用户
        # 以为「又问了一遍还是同一段」，而且模型内容换了 key 也不会失效。
        put_cached(key, build_local_blocks(trace, payload.step_index, payload.question), label)

    if timed_out:
        yield sse(
            "done",
            {"finish": "timeout", "tokens": frames, "elapsed_ms": elapsed, "degraded": True},
        )
        tutor_log.record(
            payload.trace_id,
            payload.step_index,
            payload.question,
            source=source,
            model=status["model"] if source == "llm" else None,
            latency_ms=elapsed,
            tokens=frames,
            degraded=True,
            fabricated=fabricated,
        )
        return

    if failure is not None:
        # 内容已经推出去了（本地模板或模型写了一半），最后再补一帧错误：
        # 前端据此把「来源」标成本地/不完整，并给出重试入口。
        yield sse("error", {**failure, "elapsed_ms": elapsed, "degraded": True})
        tutor_log.record(
            payload.trace_id,
            payload.step_index,
            payload.question,
            source=source,
            model=status["model"] if source == "llm" else None,
            latency_ms=elapsed,
            tokens=frames,
            degraded=True,
            fabricated=fabricated,
        )
        return

    yield sse(
        "done",
        {"finish": "stop", "tokens": frames, "elapsed_ms": elapsed, "degraded": degraded},
    )
    tutor_log.record(
        payload.trace_id,
        payload.step_index,
        payload.question,
        source=source,
        model=status["model"] if source == "llm" else None,
        latency_ms=elapsed,
        tokens=frames,
        degraded=degraded,
        fabricated=fabricated,
    )


@router.post(
    "/ask",
    summary="按当前步提问，SSE 流式返回四块讲解",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def ask(payload: TutorRequest, request: Request):
    return StreamingResponse(
        _event_stream(request, payload),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
