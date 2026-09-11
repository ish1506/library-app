import { afterEach, describe, expect, it, vi } from "vitest";
import { createBook, deleteBook, listBooks } from "./books";

const book = {
  id: 1,
  title: "Dune",
  author: "Frank Herbert",
  date: 0,
  isbn: "9780441013593",
  loan_duration_days: 14,
  total_copies: 2,
  available_copies: 2,
  late_fee_cents_per_day: 50,
};

describe("books API", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("lists books with the bearer token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(listBooks("secret-token")).resolves.toEqual([book]);
    expect(fetchMock).toHaveBeenCalledWith("/books", {
      headers: { Authorization: "Bearer secret-token" },
    });
  });

  it("encodes supplied text and inclusive date filters", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await listBooks("secret-token", {
      q: '  Dune "part two" -film ',
      date_from: "2024-01-01T00:00:00Z",
      date_to: "2024-01-31T23:59:59Z",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/books?q=Dune+%22part+two%22+-film&date_from=2024-01-01T00%3A00%3A00Z&date_to=2024-01-31T23%3A59%3A59Z",
      { headers: { Authorization: "Bearer secret-token" } },
    );
  });

  it.each([
    ['title', 'asc'], ['title', 'desc'],
    ['author', 'asc'], ['author', 'desc'],
    ['date', 'asc'], ['date', 'desc'],
  ] as const)('encodes %s %s sorting', async (sort_by, sort_order) => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await listBooks('secret-token', { sort_by, sort_order })

    expect(fetchMock).toHaveBeenCalledWith(`/books?sort_by=${sort_by}&sort_order=${sort_order}`, {
      headers: { Authorization: 'Bearer secret-token' },
    })
  })

  it('combines sorting with the existing filters and omits absent sort values', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await listBooks('secret-token', {
      q: 'Dune', date_from: '2024-01-01T00:00:00Z', date_to: '2024-01-31T23:59:59Z',
      sort_by: 'author', sort_order: 'desc',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/books?q=Dune&date_from=2024-01-01T00%3A00%3A00Z&date_to=2024-01-31T23%3A59%3A59Z&sort_by=author&sort_order=desc',
      { headers: { Authorization: 'Bearer secret-token' } },
    )
  })

  it('omits blank optional filters and supports one-sided bounds', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await listBooks('secret-token', { q: '  ', date_to: '2024-01-31T23:59:59Z' })

    expect(fetchMock).toHaveBeenCalledWith('/books?date_to=2024-01-31T23%3A59%3A59Z', {
      headers: { Authorization: 'Bearer secret-token' },
    })
  })

  it('sends the create contract and handles non-JSON errors', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(book), { status: 201 }))
      .mockResolvedValueOnce(new Response('failure', { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      createBook("token", {
        title: "Dune",
        author: "Frank Herbert",
        date: "1969-03-01T00:00:00Z",
        isbn: "9780441013593",
        loan_duration_days: 14,
        total_copies: 2,
      }),
    ).resolves.toEqual(book);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/books", {
      method: "POST",
      headers: {
        Authorization: "Bearer token",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: "Dune",
        author: "Frank Herbert",
        date: "1969-03-01T00:00:00Z",
        isbn: "9780441013593",
        loan_duration_days: 14,
        total_copies: 2,
      }),
    });
    await expect(listBooks("token")).rejects.toThrow("could not complete");
  });

  it("accepts the empty 204 delete response and normalizes authorization errors", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Admin access required" }), {
          status: 403,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(deleteBook("token", 1)).resolves.toBeUndefined();
    await expect(listBooks("token")).rejects.toThrow("permission");
  });
});
