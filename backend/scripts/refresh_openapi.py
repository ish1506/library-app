#!/usr/bin/env python3
"""Regenerate the checked-in OpenAPI document from the FastAPI application."""

import json
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
project_dir = backend_dir.parent
output_path = project_dir / "docs" / "openapi.json"

# The application creates database engines during import, but schema generation
# does not connect to the database. Keep this command usable without local config.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://docs:docs@localhost/library"
)
os.environ.setdefault("JWT_SECRET_KEY", "openapi-docs-only")
sys.path.insert(0, str(backend_dir))

from main import app


def main() -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
