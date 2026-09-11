from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    WithJsonSchema,
    field_validator,
    model_validator,
)


def _parse_publication_date(value: Any) -> int:
    if not isinstance(value, str):
        raise ValueError("date must be an ISO 8601 datetime string")  # noqa: TRY004

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("date must be an ISO 8601 datetime string") from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("date must include a timezone offset")
    return int(parsed.timestamp())


def _normalize_isbn(value: str) -> str:
    normalized = value.replace("-", "").replace(" ", "")
    if len(normalized) != 13 or not normalized.isdigit():
        raise ValueError("isbn must contain exactly 13 digits")
    return normalized


class BookCreate(BaseModel):
    title: str
    author: str
    date: int
    isbn: str
    loan_duration_days: int = Field(ge=1)
    total_copies: int = Field(ge=0)

    @field_validator("title", "author")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("date", mode="before", json_schema_input_type=str)
    @classmethod
    def parse_date(cls, value: Any) -> int:
        return _parse_publication_date(value)

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, value: str) -> str:
        return _normalize_isbn(value)


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    date: int | None = None
    isbn: str | None = None
    loan_duration_days: int | None = Field(default=None, ge=1)
    total_copies: int | None = Field(default=None, ge=0)

    @field_validator("title", "author")
    @classmethod
    def non_blank(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("date", mode="before", json_schema_input_type=str)
    @classmethod
    def parse_date(cls, value: Any) -> int | None:
        if value is None:
            raise ValueError("date must be an ISO 8601 datetime string")
        return _parse_publication_date(value)

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("isbn must contain exactly 13 digits")
        return _normalize_isbn(value)

    @field_validator("loan_duration_days", "total_copies")
    @classmethod
    def positive(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("must not be null")
        return value


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    date: int
    isbn: str
    loan_duration_days: int
    total_copies: int
    available_copies: int
    late_fee_cents_per_day: int


class BookListQuery(BaseModel):
    class SortBy(StrEnum):
        TITLE = "title"
        AUTHOR = "author"
        DATE = "date"

    class SortOrder(StrEnum):
        ASC = "asc"
        DESC = "desc"

    q: str | None = None
    date_from: Annotated[
        int | None,
        WithJsonSchema(
            {"anyOf": [{"type": "string"}, {"type": "null"}]}, mode="validation"
        ),
    ] = None
    sort_by: SortBy | None = None
    sort_order: SortOrder | None = None
    date_to: Annotated[
        int | None,
        WithJsonSchema(
            {"anyOf": [{"type": "string"}, {"type": "null"}]}, mode="validation"
        ),
    ] = None

    @field_validator("q")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("q must not be blank")
        return normalized

    @field_validator("date_from", "date_to", mode="before", json_schema_input_type=str)
    @classmethod
    def parse_date_bound(cls, value: Any) -> int | None:
        if value is None:
            return None
        return _parse_publication_date(value)

    @field_validator("sort_by", "sort_order", mode="before")
    @classmethod
    def normalize_sort_option(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "BookListQuery":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must not be after date_to")
        if self.sort_order is not None and self.sort_by is None:
            raise ValueError("sort_order requires sort_by")
        return self
