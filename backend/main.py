import asyncio
import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from app.database import AsyncSessionLocal, async_engine
from app.models.book import Book
from app.models.book_reservation import BookReservation
from app.models.enums import ReservationStatus
from app.policy import library_policy
from app.routers.auth import router as auth_router
from app.routers.books import router as books_router
from app.routers.loans import router as loans_router
from app.routers.notifications import router as notifications_router
from app.routers.reservations import router as reservations_router
from app.services.reservations import expire_ready_reservations, timestamp
from fastapi import FastAPI, Request
from sqlalchemy import select

logger = logging.getLogger("uvicorn.error.library_api")
logger.setLevel(logging.DEBUG)


async def reservation_expiry_worker() -> None:
    while True:
        await asyncio.sleep(library_policy.reservations.worker_interval_seconds)
        try:
            async with AsyncSessionLocal() as db:
                book_ids = (
                    await db.scalars(
                        select(BookReservation.book_id)
                        .where(
                            BookReservation.status == ReservationStatus.READY,
                            BookReservation.expires_at_timestamp <= timestamp(),
                        )
                        .distinct()
                    )
                ).all()
                for book_id in book_ids:
                    book = await db.scalar(
                        select(Book).where(Book.id == book_id).with_for_update()
                    )
                    if book is not None:
                        await expire_ready_reservations(db, book)
                await db.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("reservation_expiry_worker_iteration_failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    worker = asyncio.create_task(reservation_expiry_worker())
    try:
        yield
    finally:
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
        await async_engine.dispose()


app = FastAPI(title="Library API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(books_router)
app.include_router(loans_router)
app.include_router(reservations_router)
app.include_router(notifications_router)


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
    matched_route = request.scope.get("route")
    route = getattr(matched_route, "path", request.url.path)
    if matched_route is None:
        logger.warning(
            "request_unmatched request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
    logger.debug(
        "request_completed request_id=%s method=%s route=%s matched=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        route,
        matched_route is not None,
        response.status_code,
        (perf_counter() - started_at) * 1_000,
    )
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
