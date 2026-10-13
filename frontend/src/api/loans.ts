import { createRequest } from './request'

export const LoanStatus = {
  BORROWED: 1,
  RETURNED: 2,
} as const

export type LoanStatusValue = (typeof LoanStatus)[keyof typeof LoanStatus]

export type BookLoan = {
  id: number
  book_id: number
  user_id: number
  loan_timestamp: number
  due_at_timestamp: number
  returned_timestamp: number | null
  status: LoanStatusValue
  late_fee_cents: number
}

export class LoansApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'LoansApiError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function isBookLoan(value: unknown): value is BookLoan {
  return (
    isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.book_id === 'number' &&
    typeof value.user_id === 'number' &&
    typeof value.loan_timestamp === 'number' &&
    typeof value.due_at_timestamp === 'number' &&
    (value.returned_timestamp === null || typeof value.returned_timestamp === 'number') &&
    (value.status === LoanStatus.BORROWED || value.status === LoanStatus.RETURNED) &&
    typeof value.late_fee_cents === 'number'
  )
}

function errorMessage(status: number, body: unknown): string {
  const detail = isRecord(body) && typeof body.detail === 'string' ? body.detail : ''
  if (status === 401) return 'Your session has expired. Sign in again.'
  if (status === 403) return detail || 'Your account cannot use member loan actions.'
  if (status === 404) return detail || 'The book or loan could not be found.'
  if (status === 409) return detail || 'That book is unavailable or already on loan.'
  return detail || 'The library service could not complete that loan request. Please try again.'
}

const request = createRequest(
  (status, body) =>
    new LoansApiError(
      status,
      status === 0
        ? 'Unable to reach the library service. Check that it is running and try again.'
        : errorMessage(status, body),
    ),
)

function validateLoan(body: unknown): BookLoan {
  if (!isBookLoan(body))
    throw new LoansApiError(0, 'The library service returned an unexpected loan response.')
  return body
}

export async function borrowBook(token: string, bookId: number): Promise<BookLoan> {
  return validateLoan(await request<unknown>(`/books/${bookId}/loans`, token, { method: 'POST' }))
}

export async function listMyLoans(token: string): Promise<BookLoan[]> {
  const body = await request<unknown>('/loans/me', token)
  if (!Array.isArray(body) || !body.every(isBookLoan)) {
    throw new LoansApiError(0, 'The library service returned an unexpected loans response.')
  }
  return body
}

export async function listBookLoans(token: string, bookId: number): Promise<BookLoan[]> {
  const body = await request<unknown>(`/books/${bookId}/loans`, token)
  if (!Array.isArray(body) || !body.every(isBookLoan)) {
    throw new LoansApiError(0, 'The library service returned an unexpected book-loans response.')
  }
  return body
}

export async function returnLoan(token: string, loanId: number): Promise<BookLoan> {
  return validateLoan(await request<unknown>(`/loans/${loanId}/return`, token, { method: 'POST' }))
}
