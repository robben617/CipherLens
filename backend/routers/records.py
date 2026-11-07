from fastapi import APIRouter

from services.records_service import summary

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("/summary")
def records_summary():
    return summary()