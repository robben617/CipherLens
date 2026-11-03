from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import init_db
from routers.aes import router


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