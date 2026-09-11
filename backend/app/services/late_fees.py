SECONDS_PER_DAY = 86_400


def calculate_late_fee_cents(
    *, due_at_timestamp: int, cutoff_timestamp: int, daily_rate_cents: int
) -> int:
    if daily_rate_cents <= 0:
        raise ValueError("daily_rate_cents must be positive")
    late_periods = max(0, (cutoff_timestamp - due_at_timestamp) // SECONDS_PER_DAY)
    return late_periods * daily_rate_cents
