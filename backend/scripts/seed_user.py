import argparse
import sys
from pathlib import Path

# Direct script execution puts only scripts/ on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import Role, User
from app.services.auth import hash_password
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a library login account")
    parser.add_argument("username")
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--role", choices=[role.value for role in Role], default=Role.USER.value
    )
    args = parser.parse_args()

    with SessionLocal.begin() as db:
        if db.scalar(select(User).where(User.username == args.username)) is not None:
            print(
                f"User {args.username!r} already exists; choose a different username.",
                file=sys.stderr,
            )
            return 1
        db.add(
            User(
                username=args.username,
                password_hash=hash_password(args.password),
                role=Role(args.role),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
