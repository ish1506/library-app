from collections.abc import Iterable

from app.database import get_db
from app.models.book import Book
from app.models.user import Role, User
from app.routers.dependencies import get_current_user, require_admin
from app.services.auth import create_access_token
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.exc import IntegrityError


class ConstraintDiagnostic:
    constraint_name = "uq_books_isbn"


class DuplicateIsbnError(Exception):
    diag = ConstraintDiagnostic()


class ScalarResult:
    def __init__(self, books: Iterable[Book]) -> None:
        self.books = list(books)

    def all(self) -> list[Book]:
        return self.books


class FakeSession:
    def __init__(self, user: User | None = None) -> None:
        self.books: dict[int, Book] = {}
        self.next_id = 1
        self.pending: Book | None = None
        self.user = user
        self.last_query: str | None = None

    async def get(self, model: type[Book] | type[User], item_id: int) -> Book | User | None:
        if model is User:
            return self.user
        assert model is Book
        return self.books.get(item_id)

    async def scalars(self, _query: object) -> ScalarResult:
        query = _query
        if "book_reservations" in str(query):
            return ScalarResult([])
        books = list(self.books.values())
        statement = str(query)
        self.last_query = statement
        params = getattr(query.compile(), "params", {})
        if "websearch_to_tsquery" in statement:
            search = params["websearch_to_tsquery_2"]
            terms = search.lower().split()
            books = [
                book
                for book in books
                if all(
                    term in {word.lower() for word in (book.title + " " + book.author).split()}
                    for term in terms
                )
            ]
        date_values = [value for value in params.values() if isinstance(value, int)]
        if "books.date >=" in statement:
            lower = date_values.pop(0)
            books = [book for book in books if book.date >= lower]
        if "books.date <=" in statement:
            upper = date_values.pop(0)
            books = [book for book in books if book.date <= upper]
        books.sort(key=lambda book: book.id)
        if "lower(books.title)" in statement:
            books.sort(
                key=lambda book: book.title.lower(),
                reverse=" DESC" in statement.split("lower(books.title)", 1)[1].split(",", 1)[0],
            )
        elif "lower(books.author)" in statement:
            books.sort(
                key=lambda book: book.author.lower(),
                reverse=" DESC" in statement.split("lower(books.author)", 1)[1].split(",", 1)[0],
            )
        elif "books.date" in statement and "ORDER BY" in statement:
            books.sort(
                key=lambda book: book.date,
                reverse="books.date DESC" in statement,
            )
        return ScalarResult(books)

    async def scalar(self, query: object) -> Book | int | None:
        if "book_reservations" in str(query):
            return None
        if "count(" in str(query):
            return 0
        return next(iter(self.books.values()), None)

    def add(self, book: Book) -> None:
        self.pending = book

    async def commit(self) -> None:
        if self.pending is not None:
            if any(book.isbn == self.pending.isbn for book in self.books.values()):
                raise IntegrityError("insert", {}, DuplicateIsbnError())
            self.pending.id = self.next_id
            self.books[self.next_id] = self.pending
            self.next_id += 1
            self.pending = None

    async def refresh(self, _book: Book) -> None:
        pass

    async def rollback(self) -> None:
        self.pending = None

    async def delete(self, book: Book) -> None:
        del self.books[book.id]


def client_for(session: FakeSession) -> TestClient:
    app.dependency_overrides[get_db] = lambda: session
    admin = lambda: User(
        id=1, username="admin", password_hash="hash", role=Role.ADMIN
    )
    app.dependency_overrides[require_admin] = admin
    app.dependency_overrides[get_current_user] = admin
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def book_payload(**overrides: object) -> dict[str, object]:
    return {
        "title": "The Left Hand of Darkness",
        "author": "Ursula K. Le Guin",
        "date": "1969-03-01T00:00:00-08:00",
        "isbn": "978-0-441-47812-5",
        "loan_duration_days": 14,
        "total_copies": 3,
        **overrides,
    }


def test_admin_can_create_list_get_update_and_delete_books() -> None:
    session = FakeSession()
    client = client_for(session)

    created = client.post("/books", json=book_payload())
    assert created.status_code == 201
    assert created.json() == {
        "id": 1,
        "title": "The Left Hand of Darkness",
        "author": "Ursula K. Le Guin",
        "date": -26409600,
        "isbn": "9780441478125",
        "loan_duration_days": 14,
        "total_copies": 3,
        "available_copies": 3,
        "late_fee_cents_per_day": 50,
    }

    assert client.get("/books").json() == [created.json()]
    assert client.get("/books/1").json() == created.json()

    updated = client.patch("/books/1", json={"title": "The Dispossessed"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "The Dispossessed"
    assert updated.json()["available_copies"] == 3

    assert client.delete("/books/1").status_code == 204
    assert client.get("/books/1").status_code == 404


def test_book_validation_normalizes_isbn_and_rejects_invalid_values() -> None:
    client = client_for(FakeSession())

    assert client.post("/books", json=book_payload(isbn="978 0 441 47812 5")).status_code == 201
    assert client.post("/books", json=book_payload(isbn="0441478123")).status_code == 422
    assert client.post("/books", json=book_payload(title="  ")).status_code == 422
    assert client.post("/books", json=book_payload(date="1969-03-01")).status_code == 422
    zero_copies = client.post(
        "/books", json=book_payload(isbn="9780306406157", total_copies=0)
    )
    assert zero_copies.status_code == 201
    assert zero_copies.json()["available_copies"] == 0


def test_duplicate_normalized_isbn_returns_a_conflict() -> None:
    client = client_for(FakeSession())
    assert client.post("/books", json=book_payload()).status_code == 201

    response = client.post("/books", json=book_payload(isbn="978 0 441 47812 5"))

    assert response.status_code == 409
    assert response.json() == {"detail": "ISBN already exists"}


def test_update_total_copies_adjusts_available_copies_by_same_delta() -> None:
    session = FakeSession()
    client = client_for(session)
    client.post("/books", json=book_payload())

    increased = client.patch("/books/1", json={"total_copies": 5})
    assert increased.status_code == 200
    assert increased.json()["total_copies"] == 5
    assert increased.json()["available_copies"] == 5

    decreased = client.patch("/books/1", json={"total_copies": 2})
    assert decreased.status_code == 200
    assert decreased.json()["total_copies"] == 2
    assert decreased.json()["available_copies"] == 2


def test_update_total_copies_cannot_reduce_available_copies_below_zero() -> None:
    session = FakeSession()
    client = client_for(session)
    client.post("/books", json=book_payload())
    session.books[1].available_copies = 1

    response = client.patch("/books/1", json={"total_copies": 1})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "total_copies cannot be reduced below checked-out copies"
    }


def test_missing_books_return_not_found() -> None:
    client = client_for(FakeSession())

    assert client.get("/books/99").status_code == 404
    assert client.patch("/books/99", json={"title": "Changed"}).status_code == 404
    assert client.delete("/books/99").status_code == 404


def test_anonymous_cannot_list_books_but_users_can() -> None:
    user = User(id=1, username="alice", password_hash="hash", role=Role.USER)
    session = FakeSession(user)
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    anonymous = client.get("/books")
    authenticated_user = client.get(
        "/books", headers={"Authorization": f"Bearer {create_access_token(user)}"}
    )

    assert anonymous.status_code == 401
    assert anonymous.headers["www-authenticate"] == "Bearer"
    assert authenticated_user.status_code == 200
    assert authenticated_user.json() == []


def test_user_can_get_a_book() -> None:
    user = User(id=1, username="alice", password_hash="hash", role=Role.USER)
    session = FakeSession(user)
    session.books[1] = Book(
        id=1,
        title="The Left Hand of Darkness",
        author="Ursula K. Le Guin",
        date=-26409600,
        isbn="9780441478125",
        loan_duration_days=14,
        total_copies=3,
        available_copies=3,
        late_fee_cents_per_day=50,
    )
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    response = client.get(
        "/books/1", headers={"Authorization": f"Bearer {create_access_token(user)}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_books_can_be_searched_and_filtered_by_date() -> None:
    session = FakeSession()
    client = client_for(session)
    client.post("/books", json=book_payload())
    client.post(
        "/books",
        json=book_payload(
            title="The Dispossessed",
            date="1974-01-01T00:00:00Z",
            isbn="9780151554658",
        ),
    )
    client.post(
        "/books",
        json=book_payload(
            title="A Wizard of Earthsea",
            date="1968-01-01T00:00:00Z",
            isbn="9780547773742",
        ),
    )

    assert [book["title"] for book in client.get("/books?q=dispossessed").json()] == [
        "The Dispossessed"
    ]
    assert len(client.get("/books?q=ursula").json()) == 3
    assert client.get("/books?q=missing").json() == []
    assert len(client.get("/books?date_from=1970-01-01T00:00:00Z").json()) == 1
    assert len(client.get("/books?date_to=1969-03-01T08:00:00Z").json()) == 2
    assert len(
        client.get(
            "/books?date_from=1969-03-01T08:00:00Z&date_to=1974-01-01T00:00:00Z"
        ).json()
    ) == 2
    assert len(
        client.get("/books?q=  ursula  &date_to=1969-03-01T08:00:00Z").json()
    ) == 2


def test_books_can_be_sorted_case_insensitively_with_id_tie_breaking() -> None:
    session = FakeSession()
    client = client_for(session)
    client.post("/books", json=book_payload(title="zeta", author="Beta", date="1970-01-01T00:00:00Z"))
    client.post(
        "/books",
        json=book_payload(
            title="Alpha",
            author="alpha",
            date="1960-01-01T00:00:00Z",
            isbn="9780151554658",
        ),
    )
    client.post(
        "/books",
        json=book_payload(
            title="alpha",
            author="Gamma",
            date="1960-01-01T00:00:00Z",
            isbn="9780547773742",
        ),
    )

    assert [book["id"] for book in client.get("/books?sort_by=title").json()] == [2, 3, 1]
    assert [book["id"] for book in client.get("/books?sort_by=title&sort_order=desc").json()] == [1, 2, 3]
    assert [book["id"] for book in client.get("/books?sort_by=author").json()] == [2, 1, 3]
    assert [book["id"] for book in client.get("/books?sort_by=date&sort_order=desc").json()] == [1, 2, 3]


def test_explicit_sort_overrides_search_relevance() -> None:
    session = FakeSession()
    client = client_for(session)
    client.post("/books", json=book_payload(title="Zulu", isbn="9780151554658"))
    client.post("/books", json=book_payload(title="Alpha", isbn="9780547773742"))

    response = client.get("/books?q=the&sort_by=title")

    assert response.status_code == 200
    assert "ts_rank_cd" not in session.last_query


def test_book_sort_query_parameters_are_validated() -> None:
    client = client_for(FakeSession())

    assert client.get("/books?sort_by=unknown").status_code == 422
    assert client.get("/books?sort_order=sideways").status_code == 422
    assert client.get("/books?sort_order=asc").status_code == 422
    assert client.get("/books?sort_by=TITLE&sort_order=DESC").status_code == 200


def test_book_search_rejects_invalid_query_parameters() -> None:
    client = client_for(FakeSession())

    assert client.get("/books?q=%20%20").status_code == 422
    assert client.get("/books?date_from=1969-03-01").status_code == 422
    assert client.get("/books?date_to=not-a-date").status_code == 422
    assert (
        client.get(
            "/books?date_from=1970-01-01T00:00:00Z&date_to=1969-01-01T00:00:00Z"
        ).status_code
        == 422
    )
