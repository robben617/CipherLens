from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from models.schemas import ErrorResponse, QuizRequest
from services import quiz_store
from services.aes_impl import AesInputError
from services.quiz_service import grade
from services.records_service import LEGACY_CLIENT_ID, normalize_client_id, record_attempt

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.get("/items", responses={500: {"model": ErrorResponse}})
def list_items():
    """题目列表。刻意不含 answer / explanation：答案不能送到浏览器。"""
    items = quiz_store.list_items()
    return {"count": len(items), "items": items}


@router.post(
    "/submit",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def submit_quiz(
    payload: QuizRequest,
    x_client_id: str | None = Header(None, alias="X-Client-Id"),
):
    try:
        client_id = normalize_client_id(x_client_id) or LEGACY_CLIENT_ID
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

    try:
        result = grade(payload)
        record_attempt(payload, result, client_id)
        return result
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
