import { describe, expect, it, vi } from 'vitest'
import {
  cancelReservation,
  confirmReservation,
  createReservation,
  listMyReservations,
  ReservationStatus,
} from './reservations'

const reservation = {
  id: 3,
  book_id: 2,
  user_id: 7,
  created_at_timestamp: 100,
  ready_at_timestamp: null,
  expires_at_timestamp: null,
  fulfilled_at_timestamp: null,
  cancelled_at_timestamp: null,
  status: ReservationStatus.PENDING,
}
const loan = {
  id: 4,
  book_id: 2,
  user_id: 7,
  loan_timestamp: 200,
  due_at_timestamp: 300,
  returned_timestamp: null,
  status: 1,
}

describe('reservations API', () => {
  it('creates a reservation', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify(reservation), { status: 201 }))
    await expect(createReservation('token', 2)).resolves.toEqual(reservation)
    expect(fetchMock).toHaveBeenCalledWith('/books/2/reservations', {
      method: 'POST',
      headers: { Authorization: 'Bearer token' },
    })
  })

  it('lists and validates reservations', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([reservation]), { status: 200 }),
    )
    await expect(listMyReservations('token')).resolves.toEqual([reservation])
  })

  it('confirms and cancels reservations', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            reservation: { ...reservation, status: ReservationStatus.FULFILLED },
            loan,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ...reservation, status: ReservationStatus.CANCELLED }), {
          status: 200,
        }),
      )
    await expect(confirmReservation('token', 3)).resolves.toEqual({
      reservation: { ...reservation, status: ReservationStatus.FULFILLED },
      loan,
    })
    await expect(cancelReservation('token', 3)).resolves.toEqual({
      ...reservation,
      status: ReservationStatus.CANCELLED,
    })
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/reservations/3/confirm', {
      method: 'POST',
      headers: { Authorization: 'Bearer token' },
    })
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/reservations/3', {
      method: 'DELETE',
      headers: { Authorization: 'Bearer token' },
    })
  })
})
