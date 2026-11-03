from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.schemas import TraceRequest, TraceResponse
from services.aes_impl import AesInputError, build_trace
from services.trace_store import remember_trace

router = APIRouter(prefix="/api/aes", tags=["aes"])


@router.post("/trace", response_model=TraceResponse)
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