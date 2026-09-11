from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    reservation_id: int | None
    created_at_timestamp: int
    read_at_timestamp: int | None
    type: NotificationType
    payload: dict
