import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger("uvicorn.error.library_api")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.username == credentials.username))
    if user is None or not verify_password(credentials.password, user.password_hash):
        logger.debug("login_failed reason=invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("login_succeeded user_id=%s", user.id)
    return TokenResponse(access_token=create_access_token(user))
