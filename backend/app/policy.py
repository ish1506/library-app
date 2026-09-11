from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class LateFeePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_rate_cents: int = Field(gt=0, strict=True)


class ReservationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hold_seconds: int = Field(gt=0, strict=True)
    worker_interval_seconds: int = Field(gt=0, strict=True)


class LibraryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    late_fees: LateFeePolicy
    reservations: ReservationPolicy


def load_policy() -> LibraryPolicy:
    policy_path = Path(__file__).resolve().parents[1] / "config" / "library.yaml"
    try:
        with policy_path.open(encoding="utf-8") as stream:
            raw: Any = yaml.safe_load(stream)
        return LibraryPolicy.model_validate(raw)
    except (OSError, yaml.YAMLError, TypeError, ValueError) as error:
        raise RuntimeError(
            f"Invalid library policy at {policy_path}: {error}"
        ) from error


library_policy = load_policy()
