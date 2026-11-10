from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from models.schemas import ErrorResponse
from services.records_service import normalize_client_id, summary

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get(
    "/summary",
    responses={500: {"model": ErrorResponse}},
)
def records_summary(
    x_client_id: str | None = Header(None, alias="X-Client-Id"),
    scope: str | None = Query(None),
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
    return summary(client_id=client_id, scope=scope)