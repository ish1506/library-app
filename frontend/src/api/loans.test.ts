import { beforeEach, describe, expect, it, vi } from 'vitest'
import { borrowBook, listMyLoans, LoansApiError, returnLoan } from './loans'

const loan = {
  id: 4,
  book_id: 2,
  user_id: 8,
  loan_timestamp: 100,
  due_at_timestamp: 200,
  returned_timestamp: null,
  status: 1 as const,
}

describe('loans API', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('borrows without a request body and sends the bearer token', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(loan), { status: 201 }))

    await expect(borrowBook('token', 2)).resolves.toEqual(loan)
    expect(fetchMock).toHaveBeenCalledWith('/books/2/loans', {
      method: 'POST',
      headers: { Authorization: 'Bearer token' },
    })
  })

  it('validates the active loan list response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify([loan]), { status: 200 }))
    await expect(listMyLoans('token')).resolves.toEqual([loan])

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ nope: true }), { status: 200 }))
    await expect(listMyLoans('token')).rejects.toMatchObject({ status: 0 })
  })

  it('normalizes conflicts and validates return responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: 'Book is unavailable' }), { status: 409 }))
    await expect(borrowBook('token', 2)).rejects.toMatchObject({
      status: 409,
      message: 'Book is unavailable',
    } satisfies Partial<LoansApiError>)

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(loan), { status: 200 }))
    await expect(returnLoan('token', 4)).resolves.toEqual(loan)
  })
})
