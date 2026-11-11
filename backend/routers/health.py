"""健康检查：前端 E 区靠它决定显示「AI」还是「本地」状态点。

只报「有没有配好」，不报 base_url、不报 key、不回显任何一段密钥 ——
这个接口是公开的，泄露一个字段就等于泄露一次攻击面。
"""

from fastapi import APIRouter

from services import llm_service

VERSION = "0.1.0"

router = APIRouter(prefix="/api", tags=["健康检查"])


@router.get("/health", summary="健康检查（只报有没有配模型，不报 key）")
async def health():
    return {
        "status": "ok",
        "version": VERSION,
        "llm": llm_service.public_status(),
    }
