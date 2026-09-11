export type Book = {
  id: number;
  title: string;
  author: string;
  date: number;
  isbn: string;
  loan_duration_days: number;
  total_copies: number;
  available_copies: number;
  late_fee_cents_per_day: number;
};

export type BookCreate = {
  title: string;
  author: string;
  date: string;
  isbn: string;
  loan_duration_days: number;
  total_copies: number;
};

export type BookUpdate = Partial<BookCreate>;

export type BookSortBy = 'title' | 'author' | 'date'
export type BookSortOrder = 'asc' | 'desc'

export type BookListFilters = {
  q?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: BookSortBy;
  sort_order?: BookSortOrder;
}

export class BooksApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "BooksApiError";
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isBook(value: unknown): value is Book {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.title === "string" &&
    typeof value.author === "string" &&
    typeof value.date === "number" &&
    typeof value.isbn === "string" &&
    typeof value.loan_duration_days === "number" &&
    typeof value.total_copies === "number" &&
    typeof value.available_copies === "number" &&
    typeof value.late_fee_cents_per_day === "number"
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function errorMessage(status: number, body: unknown): string {
  const detail =
    isRecord(body) && typeof body.detail === "string" ? body.detail : "";
  if (status === 401) return "Your session has expired. Sign in again.";
  if (status === 403)
    return "You do not have permission to perform this action.";
  if (status === 404) return detail || "The book could not be found.";
  if (status === 409) return detail || "That ISBN is already in the catalogue.";
  if (status === 422)
    return (
      detail ||
      "The book details were not accepted. Check the form and try again."
    );
  return (
    detail ||
    "The library service could not complete that request. Please try again."
  );
}

async function request<T>(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new BooksApiError(
      0,
      "Unable to reach the library service. Check that it is running and try again.",
    );
  }

  const body = response.status === 204 ? undefined : await readJson(response);
  if (!response.ok)
    throw new BooksApiError(
      response.status,
      errorMessage(response.status, body),
    );
  return body as T;
}

export async function listBooks(
  token: string,
  filters: BookListFilters = {},
): Promise<Book[]> {
  const params = new URLSearchParams();
  if (filters.q?.trim()) params.set("q", filters.q.trim());
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_order) params.set('sort_order', filters.sort_order)
  const query = params.toString();
  const body = await request<unknown>(
    query ? `/books?${query}` : "/books",
    token,
  );
  if (!Array.isArray(body) || !body.every(isBook)) {
    throw new BooksApiError(
      0,
      "The library service returned an unexpected catalogue response.",
    );
  }
  return body;
}

export async function getBook(token: string, id: number): Promise<Book> {
  const body = await request<unknown>(`/books/${id}`, token);
  if (!isBook(body))
    throw new BooksApiError(
      0,
      "The library service returned an unexpected book response.",
    );
  return body;
}

export async function createBook(
  token: string,
  book: BookCreate,
): Promise<Book> {
  const body = await request<unknown>("/books", token, {
    method: "POST",
    body: JSON.stringify(book),
  });
  if (!isBook(body))
    throw new BooksApiError(
      0,
      "The library service returned an unexpected book response.",
    );
  return body;
}

export async function updateBook(
  token: string,
  id: number,
  changes: BookUpdate,
): Promise<Book> {
  const body = await request<unknown>(`/books/${id}`, token, {
    method: "PATCH",
    body: JSON.stringify(changes),
  });
  if (!isBook(body))
    throw new BooksApiError(
      0,
      "The library service returned an unexpected book response.",
    );
  return body;
}

export async function deleteBook(token: string, id: number): Promise<void> {
  await request<undefined>(`/books/${id}`, token, { method: "DELETE" });
}
