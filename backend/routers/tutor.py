import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from models.schemas import ErrorResponse, TutorRequest
from services.trace_store import get_trace
from services.tutor_service import (
    cache_key,
    get_cached,
    iter_answer_chunks,
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


async def _error_stream(code, message):
    yield sse("error", {"code": code, "message": message})


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

    logger.info(
        "tutor ask trace_id=%s step=%s cache=%s",
        payload.trace_id,
        payload.step_index,
        bool(cached),
    )

    if cached is not None:
        yield sse(
            "meta",
            {
                "trace_id": payload.trace_id,
                "step_index": payload.step_index,
                "quotes_values": True,
                "source": "local",
                "cache": True,
                "step_label": cached["step_label"],
            },
        )
        for chunk in cached["chunks"]:
            yield sse("token", {"t": chunk})
        yield sse(
            "done",
            {
                "finish": "stop",
                "tokens": len(cached["chunks"]),
                "degraded": False,
            },
        )
        return

    yield sse(
        "meta",
        {
            "trace_id": payload.trace_id,
            "step_index": payload.step_index,
            "quotes_values": True,
            "source": "local",
            "cache": False,
            "step_label": label,
        },
    )

    chunks = []
    deadline = asyncio.get_running_loop().time() + 20.0

    try:
        for chunk in iter_answer_chunks(trace, payload.step_index, payload.question):
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
                        "finish": "stop",
                        "tokens": len(chunks),
                        "degraded": True,
                    },
                )
                return

            chunks.append(chunk)
            yield sse("token", {"t": chunk})
            await asyncio.sleep(0.03)
    except asyncio.CancelledError:
        logger.info(
            "tutor cancelled trace_id=%s step=%s",
            payload.trace_id,
            payload.step_index,
        )
        raise

    put_cached(key, chunks, label)
    yield sse(
        "done",
        {
            "finish": "stop",
            "tokens": len(chunks),
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