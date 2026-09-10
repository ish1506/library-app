import { afterEach, describe, expect, it, vi } from 'vitest'
import { createBook, deleteBook, listBooks } from './books'

const book = { id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 2, available_copies: 2 }

describe('books API', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('lists books with the bearer token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([book]), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(listBooks('secret-token')).resolves.toEqual([book])
    expect(fetchMock).toHaveBeenCalledWith('/books', {
      headers: { Authorization: 'Bearer secret-token' },
    })
  })

  it('sends the create contract and handles non-JSON errors', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(book), { status: 201 }))
      .mockResolvedValueOnce(new Response('failure', { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(createBook('token', {
      title: 'Dune', author: 'Frank Herbert', date: '1969-03-01T00:00:00Z',
      isbn: '9780441013593', loan_duration_days: 14, total_copies: 2,
    })).resolves.toEqual(book)
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/books', {
      method: 'POST',
      headers: { Authorization: 'Bearer token', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Dune', author: 'Frank Herbert', date: '1969-03-01T00:00:00Z',
        isbn: '9780441013593', loan_duration_days: 14, total_copies: 2,
      }),
    })
    await expect(listBooks('token')).rejects.toThrow('could not complete')
  })

  it('accepts the empty 204 delete response and normalizes authorization errors', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Admin access required' }), { status: 403 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(deleteBook('token', 1)).resolves.toBeUndefined()
    await expect(listBooks('token')).rejects.toThrow('permission')
  })
})
