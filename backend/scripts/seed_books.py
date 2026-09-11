"""Acquire and seed a small, deterministic catalogue from Open Library."""

import argparse
import csv
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx

# Direct script execution puts only scripts/ on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "seed_cache"
DEFAULT_CSV = ROOT / "seed_books.csv"
CSV_COLUMNS = (
    "source_key",
    "title",
    "author",
    "date",
    "isbn",
    "loan_duration_days",
    "total_copies",
    "available_copies",
)
USER_AGENT = "library-app-open-library-seeder/1.0 (contact: library-app@example.com)"

MANIFEST_PATH = ROOT / "seed_data" / "famous_books.json"
TITLES = tuple(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))
# Keep accidental manifest edits from silently producing a partial seed.
assert len(TITLES) == 100 and len({title.casefold() for title in TITLES}) == 100


def source_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")


def comparable_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def isbn13(value: Any) -> str | None:
    digits = re.sub(r"[-\s]", "", str(value)) if value is not None else ""
    return digits if len(digits) == 13 and digits.isdigit() else None


def choose_isbn(values: Iterable[Any]) -> str | None:
    for value in values:
        result = isbn13(value)
        if result:
            return result
    return None


def date_to_timestamp(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    match = re.fullmatch(r"(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?", text)
    if not match:
        return 0
    year = int(match.group(1))
    month = int(match.group(2) or 1)
    day = int(match.group(3) or 1)
    try:
        timestamp = int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())
        return timestamp if -(2**63) <= timestamp <= 2**63 - 1 else 0
    except ValueError:
        return 0


def document_isbns(document: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for key in ("isbn", "isbn13", "isbn_13"):
        value = document.get(key, [])
        values.extend(value if isinstance(value, list) else [value])
    return values


def select_work(
    documents: list[dict[str, Any]], requested_title: str
) -> dict[str, Any] | None:
    requested = comparable_title(requested_title)
    candidates = []
    for index, document in enumerate(documents):
        isbn = choose_isbn(document_isbns(document))
        if not isbn:
            continue
        title = str(document.get("title") or "").strip()
        normalized = comparable_title(title)
        exact = normalized == requested
        starts = normalized.startswith(requested) or requested.startswith(normalized)
        # Sorting is explicit so response ordering cannot change the selected edition.
        score = (
            int(exact),
            int(starts),
            int(bool(document.get("author_name"))),
            int(bool(document.get("first_publish_year"))),
        )
        candidates.append((score, -len(title), isbn, index, document))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[:4])[-1]


def normalize_document(document: dict[str, Any], title: str) -> dict[str, Any] | None:
    isbn = choose_isbn(document_isbns(document))
    if not isbn:
        return None
    authors = document.get("author_name") or []
    author = str(authors[0]).strip() if authors else "Unknown Author"
    publish_dates = document.get("publish_date") or []
    publish_date = publish_dates[0] if publish_dates else None
    if not isinstance(publish_dates, list):
        publish_date = publish_dates
    date = date_to_timestamp(publish_date)
    if date == 0:
        date = date_to_timestamp(document.get("first_publish_year"))
    return {
        "source_key": str(document.get("key") or source_key(title)),
        "title": str(document.get("title") or title).strip() or title,
        "author": author or "Unknown Author",
        "date": date,
        "isbn": isbn,
        "loan_duration_days": 14,
        "total_copies": 1,
        "available_copies": 1,
    }


def acquire_manifest(
    *,
    refresh: bool = False,
    cache_dir: Path = CACHE_DIR,
    client: Any = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, list[dict[str, Any]]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    owned_client = client is None
    client = client or httpx.Client(timeout=20, headers={"User-Agent": user_agent()})
    results: dict[str, list[dict[str, Any]]] = {}
    try:
        for index, title in enumerate(TITLES):
            key = source_key(title)
            path = cache_dir / f"{key}.json"
            if path.exists() and not refresh:
                results[key] = json.loads(path.read_text(encoding="utf-8")).get(
                    "docs", []
                )
                continue
            if index:
                sleep(0.2)
            url = (
                "https://openlibrary.org/search.json?title="
                + quote_plus(title)
                + "&limit=20&fields=key,title,author_name,first_publish_year,publish_date,isbn"
            )
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    results[key] = payload.get("docs", [])
                    break
                except (httpx.HTTPError, ValueError, OSError) as error:
                    last_error = error
                    if attempt < 2:
                        sleep(0.5 * (2**attempt))
            else:
                raise RuntimeError(
                    f"Unable to acquire {title}: {last_error}"
                ) from last_error
    finally:
        if owned_client:
            client.close()
    return results


def normalize_batch(
    raw: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows, reports = [], []
    seen: set[str] = set()
    for title in TITLES:
        key = source_key(title)
        document = select_work(raw.get(key, []), title)
        row = normalize_document(document, title) if document else None
        if row is None:
            reports.append(f"{title}: missing ISBN-13 or usable Open Library result")
            continue
        if row["isbn"] in seen:
            reports.append(f"{title}: duplicate ISBN-13 {row['isbn']}")
            continue
        seen.add(row["isbn"])
        rows.append(row)
    return rows, reports


def validate_batch(rows: list[dict[str, Any]]) -> None:
    if len(rows) != len({row["isbn"] for row in rows}):
        raise ValueError("batch contains duplicate ISBN-13 values")
    missing = [column for row in rows for column in CSV_COLUMNS if column not in row]
    if missing:
        raise ValueError(f"batch is missing columns: {sorted(set(missing))}")
    if any(not isbn13(row["isbn"]) for row in rows):
        raise ValueError("batch contains malformed ISBN-13 values")


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    validate_batch(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(
            {column: row[column] for column in CSV_COLUMNS} for row in rows
        )


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ("date", "loan_duration_days", "total_copies", "available_copies"):
            row[key] = int(row[key])
    validate_batch(rows)
    return rows


def load_books(
    rows: list[dict[str, Any]], session_factory: Any = None, dry_run: bool = False
) -> int:
    validate_batch(rows)
    if dry_run:
        return len(rows)
    if session_factory is None:
        from app.database import SessionLocal

        session_factory = SessionLocal
    from sqlalchemy import select

    inserted = 0
    with session_factory.begin() as db:
        from app.models.book import Book
        from app.policy import library_policy

        existing = set(db.scalars(select(Book.isbn)).all())
        for row in rows:
            if row["isbn"] not in existing:
                db.add(
                    Book(
                        **{key: row[key] for key in CSV_COLUMNS if key != "source_key"},
                        late_fee_cents_per_day=library_policy.late_fees.daily_rate_cents,
                    )
                )
                existing.add(row["isbn"])
                inserted += 1
    return inserted


def user_agent() -> str:
    email = os.getenv("OPEN_LIBRARY_CONTACT_EMAIL", "library-app@example.com")
    return f"library-app-open-library-seeder/1.0 (contact: {email})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed famous books from Open Library")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--fetch", action="store_true", help="fetch/cache and export the default CSV"
    )
    modes.add_argument(
        "--load", action="store_true", help="load --csv PATH, or the default CSV"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="export to PATH, or load PATH with --load",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="ignore cached responses (only with --fetch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and report without database writes",
    )
    args = parser.parse_args(argv)
    if not (args.fetch or args.load or args.csv):
        parser.error("one of --fetch, --csv, or --load is required")
    if args.refresh and not args.fetch:
        parser.error("--refresh requires --fetch")
    output = args.csv or DEFAULT_CSV
    if (args.fetch or args.csv) and not args.load:
        raw = acquire_manifest(refresh=args.refresh)
        rows, reports = normalize_batch(raw)
        for report in reports:
            print(f"WARNING: {report}", file=sys.stderr)
        validate_batch(rows)
        write_csv(rows, output)
        print(f"Wrote {len(rows)} rows to {output}")
        return 0
    rows = read_csv(output)
    count = load_books(rows, dry_run=args.dry_run)
    print(f"{'Would load' if args.dry_run else 'Loaded'} {count} books from {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
