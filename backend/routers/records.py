from fastapi import APIRouter

from models.schemas import ErrorResponse

from services.records_service import summary

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get(
    "/summary",
    responses={500: {"model": ErrorResponse}},
)
def records_summary():
    return summary()