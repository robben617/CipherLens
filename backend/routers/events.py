import logging

from fastapi import APIRouter, Response

from models.schemas import ErrorResponse, EventsRequest

logger = logging.getLogger("cipherlens.events")

router = APIRouter(prefix="/api", tags=["events"])


@router.post(
    "/events",
    status_code=204,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ingest_events(payload: EventsRequest):
    logger.info(
        "events received session_id=%s count=%s",
        payload.session_id,
        len(payload.items),
    )
    # B3 只交付批量上报线；session_id 是字符串（如 s_9c21），
    # 与 sessions.id 的整数主键映射后再落 step_events，避免此时硬造会话。
    return Response(status_code=204)