import enum


class LoanStatus(enum.IntEnum):
    BORROWED = 1
    RETURNED = 2


class ReservationStatus(enum.IntEnum):
    PENDING = 1
    READY = 2
    FULFILLED = 3
    CANCELLED = 4
    EXPIRED = 5


class NotificationType(enum.IntEnum):
    RESERVATION_READY = 1


class Role(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
