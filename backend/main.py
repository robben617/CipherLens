from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from db import init_db
from env_file import load_env_file
from routers.aes import router
from routers.events import router as events_router
from routers.glossary import router as glossary_router
from routers.health import VERSION, router as health_router
from routers.quiz import router as quiz_router
from routers.records import router as records_router
from routers.tutor import router as tutor_router
from services.quiz_store import seed_items

# 必须在任何一次 services.*.config() 之前跑；没有 .env 时是空操作。
load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("cipherlens.tutor").setLevel(logging.INFO)

logger = logging.getLogger("cipherlens.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # 题库以 quiz_bank.py 为准，答案用当前引擎现算后灌库
    seed_items()
    yield


# 文档与 schema 必须挂在 /api 下：生产环境 nginx 只反代 /api/，默认的
# /docs、/openapi.json 会直接 404（大赛「接口文档」一项就是卡在这）。
#
# Swagger 的 css/js 也不吃默认 CDN：评审机常常不能联外网，CDN 一断就是一页
# 裸 HTML（实测 CSS 被 reset 过）。资源随镜像走，离线可用。
# 注意：swagger_js_url / swagger_css_url 是 get_swagger_ui_html() 的参数，
# 不是 FastAPI() 的构造参数——写进构造函数不报错，会被 **extra 静默吞掉。
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="CipherLens API",
    description="AES 可视化教学工作台的接口。前端只渲染，算法与判分都在这里。",
    version=VERSION,
    lifespan=lifespan,
    docs_url=None,  # 关掉内置 /docs，改用下面的 swagger_docs()
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")

SWAGGER_UI_PARAMS = {
    "docExpansion": "list",
    "defaultModelsExpandDepth": -1,
    "displayRequestDuration": True,
}


@app.get("/api/docs", include_in_schema=False)
async def swagger_docs():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} · 接口文档",
        swagger_js_url="/api/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/api/static/swagger/swagger-ui.css",
        swagger_favicon_url="/api/static/swagger/favicon-32x32.png",
        swagger_ui_parameters=SWAGGER_UI_PARAMS,
    )

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
app.include_router(glossary_router)
app.include_router(health_router)


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