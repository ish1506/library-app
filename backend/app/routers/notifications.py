from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.routers.dependencies import require_user
from app.schemas.notification import NotificationResponse
from app.services.reservations import timestamp

router = APIRouter(prefix="/notifications", tags=["notifications"])
USER_DEPENDENCY = Depends(require_user)
DB_DEPENDENCY = Depends(get_db)


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> list[Notification]:
    statement = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        statement = statement.where(Notification.read_at_timestamp.is_(None))
    return (
        await db.scalars(
            statement.order_by(
                Notification.created_at_timestamp.desc(), Notification.id.desc()
            ).limit(limit)
        )
    ).all()


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Notification:
    notification = await db.scalar(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .with_for_update()
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    if notification.read_at_timestamp is None:
        notification.read_at_timestamp = timestamp()
        await db.commit()
        await db.refresh(notification)
    return notification
