from app.routers.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(title="Library API", version="0.1.0")
app.include_router(auth_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
