from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.schemas import QuizRequest
from services.aes_impl import AesInputError
from services.quiz_service import grade

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/submit")
def submit_quiz(payload: QuizRequest):
    try:
        return grade(payload)
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