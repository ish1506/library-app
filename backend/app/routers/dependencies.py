import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import Role, User

bearer_scheme = HTTPBearer(auto_error=False)
BEARER_DEPENDENCY = Depends(bearer_scheme)
DB_DEPENDENCY = Depends(get_db)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = BEARER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> User:
    if credentials is None:
        raise unauthorized()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "role"]},
        )
        user_id = int(payload["sub"])
        Role(payload["role"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized() from None

    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized()
    return user


CURRENT_USER_DEPENDENCY = Depends(get_current_user)


async def require_admin(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if user.role is not Role.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )
    return user
