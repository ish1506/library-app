import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from app.database import async_engine
from app.routers.auth import router as auth_router
from app.routers.books import router as books_router
from fastapi import FastAPI, Request

logger = logging.getLogger("uvicorn.error.library_api")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await async_engine.dispose()


app = FastAPI(title="Library API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(books_router)


@app.middleware("http")
async def log_request(request: Request, call_next):
    request_id = uuid4().hex
    started_at = perf_counter()
    logger.debug(
        "request_started request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            (perf_counter() - started_at) * 1_000,
        )
        raise

    response.headers["X-Request-ID"] = request_id
    route = getattr(request.scope.get("route"), "path", request.url.path)
    logger.debug(
        "request_completed request_id=%s method=%s route=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        route,
        response.status_code,
        (perf_counter() - started_at) * 1_000,
    )
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
