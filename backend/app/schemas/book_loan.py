from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LoanStatus


class BookLoanRequest(BaseModel):
    user_rating: int = Field(ge=1, le=5)


class BookLoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    loan_timestamp: int
    due_at_timestamp: int
    returned_timestamp: int | None
    status: LoanStatus
    late_fee_cents: int
