from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import init_db
from routers.aes import router
from routers.events import router as events_router
from routers.quiz import router as quiz_router
from routers.records import router as records_router
from routers.tutor import router as tutor_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("cipherlens.tutor").setLevel(logging.INFO)

logger = logging.getLogger("cipherlens.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CipherLens API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(tutor_router)
app.include_router(quiz_router)
app.include_router(events_router)
app.include_router(records_router)


def _field_from_location(location):
    parts = list(location or [])
    if "plaintext_hex" in parts:
        return "plaintext"
    if "key_hex" in parts or "key_bits" in parts:
        return "key"
    return None


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "validation_error",
                "message": first.get("msg", "invalid request"),
                "field": _field_from_location(first.get("loc")),
            }
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _exc: Exception):
    logger.exception(
        "unhandled error path=%s method=%s",
        _request.url.path,
        _request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "internal server error",
                "field": None,
            }
        },
    )