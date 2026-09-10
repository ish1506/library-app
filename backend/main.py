from contextlib import asynccontextmanager

from app.database import async_engine
from app.routers.auth import router as auth_router
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await async_engine.dispose()


app = FastAPI(title="Library API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
