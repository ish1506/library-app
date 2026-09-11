import type { BookLoan } from './loans'

export const ReservationStatus = {
  PENDING: 1,
  READY: 2,
  FULFILLED: 3,
  CANCELLED: 4,
  EXPIRED: 5,
} as const

export type ReservationStatusValue = (typeof ReservationStatus)[keyof typeof ReservationStatus]

export type BookReservation = {
  id: number
  book_id: number
  user_id: number
  created_at_timestamp: number
  ready_at_timestamp: number | null
  expires_at_timestamp: number | null
  fulfilled_at_timestamp: number | null
  cancelled_at_timestamp: number | null
  status: ReservationStatusValue
}

export type ReservationConfirmation = {
  reservation: BookReservation
  loan: BookLoan
}

export class ReservationsApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ReservationsApiError'
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function isBookReservation(value: unknown): value is BookReservation {
  return (
    isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.book_id === 'number' &&
    typeof value.user_id === 'number' &&
    typeof value.created_at_timestamp === 'number' &&
    (value.ready_at_timestamp === null || typeof value.ready_at_timestamp === 'number') &&
    (value.expires_at_timestamp === null || typeof value.expires_at_timestamp === 'number') &&
    (value.fulfilled_at_timestamp === null || typeof value.fulfilled_at_timestamp === 'number') &&
    (value.cancelled_at_timestamp === null || typeof value.cancelled_at_timestamp === 'number') &&
    Object.values(ReservationStatus).includes(value.status as ReservationStatusValue)
  )
}

function isBookLoan(value: unknown): value is BookLoan {
  return (
    isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.book_id === 'number' &&
    typeof value.user_id === 'number' &&
    typeof value.loan_timestamp === 'number' &&
    typeof value.due_at_timestamp === 'number' &&
    (value.returned_timestamp === null || typeof value.returned_timestamp === 'number') &&
    (value.status === 1 || value.status === 2)
  )
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

function errorMessage(status: number, body: unknown): string {
  const detail = isRecord(body) && typeof body.detail === 'string' ? body.detail : ''
  if (status === 401) return 'Your session has expired. Sign in again.'
  if (status === 403) return detail || 'Your account cannot use member reservation actions.'
  if (status === 404) return detail || 'The reservation or book could not be found.'
  if (status === 409) return detail || 'That reservation cannot be completed in its current state.'
  return (
    detail || 'The library service could not complete that reservation request. Please try again.'
  )
}

async function request<T>(
  path: string,
  token: string,
  method: 'GET' | 'POST' | 'DELETE',
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ReservationsApiError(
      0,
      'Unable to reach the library service. Check that it is running and try again.',
    )
  }

  const body = response.status === 204 ? undefined : await readJson(response)
  if (!response.ok)
    throw new ReservationsApiError(response.status, errorMessage(response.status, body))
  return body as T
}

export async function createReservation(token: string, bookId: number): Promise<BookReservation> {
  const body = await request<unknown>(`/books/${bookId}/reservations`, token, 'POST')
  if (!isBookReservation(body))
    throw new ReservationsApiError(
      0,
      'The library service returned an unexpected reservation response.',
    )
  return body
}

export async function listMyReservations(token: string): Promise<BookReservation[]> {
  const body = await request<unknown>('/reservations/me?limit=50', token, 'GET')
  if (!Array.isArray(body) || !body.every(isBookReservation)) {
    throw new ReservationsApiError(
      0,
      'The library service returned an unexpected reservations response.',
    )
  }
  return body
}

export async function confirmReservation(
  token: string,
  reservationId: number,
): Promise<ReservationConfirmation> {
  const body = await request<unknown>(`/reservations/${reservationId}/confirm`, token, 'POST')
  if (!isRecord(body) || !isBookReservation(body.reservation) || !isBookLoan(body.loan)) {
    throw new ReservationsApiError(
      0,
      'The library service returned an unexpected confirmation response.',
    )
  }
  return { reservation: body.reservation, loan: body.loan }
}

export async function cancelReservation(
  token: string,
  reservationId: number,
): Promise<BookReservation> {
  const body = await request<unknown>(`/reservations/${reservationId}`, token, 'DELETE')
  if (!isBookReservation(body))
    throw new ReservationsApiError(
      0,
      'The library service returned an unexpected reservation response.',
    )
  return body
}
