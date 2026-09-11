from pydantic import BaseModel, ConfigDict

from app.models.book_reservation import ReservationStatus
from app.schemas.book_loan import BookLoanResponse


class BookReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    created_at_timestamp: int
    ready_at_timestamp: int | None
    expires_at_timestamp: int | None
    fulfilled_at_timestamp: int | None
    cancelled_at_timestamp: int | None
    status: ReservationStatus


class ReservationConfirmationResponse(BaseModel):
    reservation: BookReservationResponse
    loan: BookLoanResponse
