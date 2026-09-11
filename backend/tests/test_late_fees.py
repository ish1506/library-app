import pytest
from app.services.late_fees import calculate_late_fee_cents


@pytest.mark.parametrize(
    ("cutoff", "expected"),
    [
        (1_000, 0),
        (1_001, 0),
        (1_000 + 86_399, 0),
        (1_000 + 86_400, 50),
        (1_000 + 172_800, 100),
    ],
)
def test_late_fee_uses_complete_periods(cutoff: int, expected: int) -> None:
    assert (
        calculate_late_fee_cents(
            due_at_timestamp=1_000,
            cutoff_timestamp=cutoff,
            daily_rate_cents=50,
        )
        == expected
    )


def test_late_fee_uses_return_cutoff_and_rejects_invalid_rate() -> None:
    assert (
        calculate_late_fee_cents(
            due_at_timestamp=1_000,
            cutoff_timestamp=1_000 + 86_400 * 3 + 1,
            daily_rate_cents=75,
        )
        == 225
    )
    with pytest.raises(ValueError):
        calculate_late_fee_cents(
            due_at_timestamp=1_000,
            cutoff_timestamp=1_001,
            daily_rate_cents=0,
        )
