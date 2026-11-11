from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from models.schemas import ErrorResponse
from services.records_service import clear_records, normalize_client_id, summary

router = APIRouter(prefix="/api/records", tags=["records"])


def _bad_client_id():
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
        return _bad_client_id()
    return summary(client_id=client_id, scope=scope)


@router.delete(
    "",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_records(x_client_id: str | None = Header(None, alias="X-Client-Id")):
    """清空本机记录：只删自己 client_id 下的数据，迁移前数据不给删。"""
    try:
        client_id = normalize_client_id(x_client_id)
    except ValueError:
        return _bad_client_id()

    if client_id is None:
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

    try:
        removed = clear_records(client_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "legacy_scope_readonly",
                    "message": "迁移前记录只能查看，不能删除",
                    "field": None,
                }
            },
        )

    return {"removed": removed}
