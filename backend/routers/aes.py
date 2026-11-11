from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.schemas import ErrorResponse, TraceRequest, TraceResponse
from services.aes_impl import AesInputError, build_trace
from services.trace_store import remember_trace

router = APIRouter(prefix="/api/aes", tags=["AES 轨迹"])


@router.post(
    "/trace",
    summary="生成一轮完整轨迹（加密 41 步 / 解密 41 步）",
    response_model=TraceResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def create_trace(payload: TraceRequest):
    try:
        trace = build_trace(
            payload.plaintext_hex,
            payload.key_hex,
            payload.key_bits,
            payload.direction,
        )
        remember_trace(trace)
        return trace
    except AesInputError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "field": exc.field,
                }
            },
        )