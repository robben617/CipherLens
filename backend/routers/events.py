from fastapi import APIRouter, Header, Response
from fastapi.responses import JSONResponse

from models.schemas import ErrorResponse, EventsRequest
from services.event_service import record_events
from services.records_service import normalize_client_id

router = APIRouter(prefix="/api", tags=["events"])


@router.post(
    "/events",
    status_code=204,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ingest_events(
    payload: EventsRequest,
    x_client_id: str | None = Header(None, alias="X-Client-Id"),
):
    try:
        client_id = normalize_client_id(x_client_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "invalid_client_id",
                    "message": "X-Client-Id must match c_<32 lowercase hex>",
                    "field": "X-Client-Id",
                }
            },
        )

    if client_id is None:
        # 没有 client_id 就没法归属：宁可报错，也不写一行不知道是谁的事件
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "missing_client_id",
                    "message": "X-Client-Id is required",
                    "field": "X-Client-Id",
                }
            },
        )

    record_events(client_id, payload.items)
    return Response(status_code=204)
