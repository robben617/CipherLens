from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.schemas import (
    AvalancheRequest,
    AvalancheResponse,
    AvalancheSweepRequest,
    AvalancheSweepResponse,
    ErrorResponse,
)
from services.aes_impl import AesInputError
from services.avalanche_service import compare, sweep

router = APIRouter(prefix="/api/aes", tags=["雪崩实验"])


def _error(exc):
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


@router.post(
    "/avalanche",
    summary="改 1 位，对比两条密文的差异（位级）",
    response_model=AvalancheResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def create_avalanche(payload: AvalancheRequest):
    """把 target 指定的那一块输入翻 1 位，各自加密，返回差异。

    返回 128 个 bit_flags 而不是只给一个百分比：只给「49%」是结论，
    给到位图才是证据 —— 哪一位变了、哪一个字节变了几位，都能看见。
    """
    try:
        return compare(
            payload.plaintext_hex,
            payload.key_hex,
            payload.target,
            payload.byte_index,
            payload.bit_index,
        )
    except AesInputError as exc:
        return _error(exc)


@router.post(
    "/avalanche/sweep",
    summary="逐字节各改 1 位，统计 16/24/32 次的平均变化位数",
    response_model=AvalancheSweepResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def create_avalanche_sweep(payload: AvalancheSweepRequest):
    """单次实验可能撞上 58 位，看起来像巧合；连做一轮取平均才说明「设计如此」。"""
    try:
        return sweep(
            payload.plaintext_hex,
            payload.key_hex,
            payload.target,
            payload.bit_index,
        )
    except AesInputError as exc:
        return _error(exc)
