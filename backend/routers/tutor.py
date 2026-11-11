import asyncio
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from models.schemas import ErrorResponse, TutorRequest
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

router = APIRouter(prefix="/api/tutor", tags=["tutor"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# 每帧之间的间隔。原来恒为 30ms 且内容固定，看着像加载条；
# 现在帧数随正文长度变，间隔略缩，四块讲完约 2 秒。
FRAME_DELAY = 0.025


def _meta(payload, step, label, cached):
    return {
        "trace_id": payload.trace_id,
        "step_index": payload.step_index,
        "step_label": label,
        "quotes_values": True,
        "source": "local",
        "model": None,
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
    label = step_label(step)
    key = cache_key(payload.trace_id, payload.step_index, payload.question)
    cached = get_cached(key)
    started = time.perf_counter()

    logger.info(
        "tutor ask trace_id=%s step=%s cache=%s",
        payload.trace_id,
        payload.step_index,
        bool(cached),
    )

    if cached is not None:
        yield sse("meta", _meta(payload, step, cached["step_label"], True))
        # 命中缓存不走逐字：缓存的意义就是立刻拿到，再慢慢打一遍反而像没命中。
        for block in cached["blocks"]:
            yield sse("block", block)
        yield sse(
            "done",
            {
                "finish": "stop",
                "tokens": len(cached["blocks"]),
                "elapsed_ms": 0,
                "degraded": False,
            },
        )
        return

    yield sse("meta", _meta(payload, step, label, False))

    blocks = build_local_blocks(trace, payload.step_index, payload.question)
    frames = 0
    deadline = asyncio.get_running_loop().time() + 20.0

    try:
        for event, data in iter_block_events(trace, payload.step_index, payload.question):
            if await request.is_disconnected():
                logger.info(
                    "tutor cancelled trace_id=%s step=%s",
                    payload.trace_id,
                    payload.step_index,
                )
                return

            if asyncio.get_running_loop().time() >= deadline:
                yield sse(
                    "done",
                    {
                        "finish": "timeout",
                        "tokens": frames,
                        "elapsed_ms": int((time.perf_counter() - started) * 1000),
                        "degraded": True,
                    },
                )
                return

            yield sse(event, data)
            # only token frames pace the stream; block frames are structural
            if event == "token":
                frames += 1
                await asyncio.sleep(FRAME_DELAY)
    except asyncio.CancelledError:
        logger.info(
            "tutor cancelled trace_id=%s step=%s",
            payload.trace_id,
            payload.step_index,
        )
        raise

    put_cached(key, blocks, label)
    yield sse(
        "done",
        {
            "finish": "stop",
            "tokens": frames,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "degraded": False,
        },
    )


@router.post(
    "/ask",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def ask(payload: TutorRequest, request: Request):
    return StreamingResponse(
        _event_stream(request, payload),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
