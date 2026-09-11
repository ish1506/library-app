import { describe, expect, it, vi } from 'vitest'
import { listUnreadNotifications, markNotificationRead, NotificationType } from './notifications'

const notification = {
  id: 5,
  user_id: 7,
  reservation_id: 3,
  created_at_timestamp: 100,
  read_at_timestamp: null,
  type: NotificationType.RESERVATION_READY,
  payload: { title: 'Dune', author: 'Frank Herbert', expires_at_timestamp: 200 },
}

describe('notifications API', () => {
  it('lists unread notifications', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify([notification]), { status: 200 }))
    await expect(listUnreadNotifications('token')).resolves.toEqual([notification])
    expect(fetchMock).toHaveBeenCalledWith('/notifications?unread_only=true&limit=50', {
      method: 'GET',
      headers: { Authorization: 'Bearer token' },
    })
  })

  it('marks a notification read', async () => {
    const read = { ...notification, read_at_timestamp: 300 }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(read), { status: 200 }),
    )
    await expect(markNotificationRead('token', notification.id)).resolves.toEqual(read)
  })
})
