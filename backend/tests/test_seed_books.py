import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "seed_books", Path(__file__).parents[1] / "scripts" / "seed_books.py"
)
seed_books = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(seed_books)


def document(title="Pride and Prejudice", isbn="9780141439518", author="Jane Austen"):
    return {
        "title": title,
        "isbn": [isbn],
        "author_name": [author],
        "publish_date": ["1813-01-28"],
    }


def row(isbn="9780141439518"):
    return {
        "source_key": "pride-and-prejudice",
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "date": 1359331200,
        "isbn": isbn,
        "loan_duration_days": 14,
        "total_copies": 1,
        "available_copies": 1,
    }


def test_date_conversion_and_defaults():
    assert seed_books.date_to_timestamp("1970-01-02") == 86400
    assert seed_books.date_to_timestamp("not-a-date") == 0
    assert seed_books.date_to_timestamp("1792-01-01") == -5617123200
    normalized = seed_books.normalize_document(
        {"isbn": ["9780141439518"]}, "Pride and Prejudice"
    )
    assert normalized["author"] == "Unknown Author"
    assert normalized["date"] == 0
    assert normalized["loan_duration_days"] == 14
    assert normalized["total_copies"] == normalized["available_copies"] == 1


def test_normalization_records_open_library_key():
    normalized = seed_books.normalize_document(
        {
            "key": "/works/OL123W",
            "title": "Pride and Prejudice",
            "isbn": ["9780141439518"],
        },
        "Pride and Prejudice",
    )
    assert normalized["source_key"] == "/works/OL123W"


def test_normalization_falls_back_to_publish_year():
    normalized = seed_books.normalize_document(
        {
            "isbn": ["9780141439518"],
            "publish_date": ["not-a-date"],
            "first_publish_year": 1813,
        },
        "Pride and Prejudice",
    )
    assert normalized["date"] == seed_books.date_to_timestamp("1813")


def test_isbn_selection_and_normalization():
    assert (
        seed_books.choose_isbn(["0306406152", "978-0-306-40615-7"]) == "9780306406157"
    )
    assert (
        seed_books.normalize_document(
            document(isbn="978-0-14-143951-8"), "Pride and Prejudice"
        )["isbn"]
        == "9780141439518"
    )
    assert (
        seed_books.normalize_document(document(isbn="bad"), "Pride and Prejudice")
        is None
    )


def test_selection_prefers_exact_title_and_metadata():
    selected = seed_books.select_work(
        [document("Pride"), document("Pride and Prejudice", author="Jane Austen")],
        "Pride and Prejudice",
    )
    assert selected["title"] == "Pride and Prejudice"


def test_batch_reports_duplicate_isbn():
    raw = {seed_books.source_key(title): [] for title in seed_books.TITLES}
    raw[seed_books.source_key(seed_books.TITLES[0])] = [document()]
    raw[seed_books.source_key(seed_books.TITLES[1])] = [document("1984")]
    rows, reports = seed_books.normalize_batch(raw)
    assert len(rows) == 1
    assert any("duplicate ISBN-13" in report for report in reports)


def test_dry_run_does_not_open_session():
    assert seed_books.load_books([row()], dry_run=True) == 1


def test_transaction_failure_propagates_and_rolls_back():
    class BrokenSessionFactory:
        @staticmethod
        def begin():
            class Context:
                def __enter__(self):
                    raise RuntimeError("database unavailable")

                def __exit__(self, *args):
                    return False

            return Context()

    with pytest.raises(RuntimeError, match="database unavailable"):
        seed_books.load_books([row()], session_factory=BrokenSessionFactory)
