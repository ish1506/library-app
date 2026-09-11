from pydantic import BaseModel, ConfigDict

from app.models.book_loan import LoanStatus


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
