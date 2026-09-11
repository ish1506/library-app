export const NotificationType = { RESERVATION_READY: 1 } as const
export type NotificationTypeValue = typeof NotificationType[keyof typeof NotificationType]

export type Notification = {
  id: number
  user_id: number
  reservation_id: number | null
  created_at_timestamp: number
  read_at_timestamp: number | null
  type: NotificationTypeValue
  payload: Record<string, unknown>
}

export class NotificationsApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'NotificationsApiError'
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function isNotification(value: unknown): value is Notification {
  return isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.user_id === 'number' &&
    (value.reservation_id === null || typeof value.reservation_id === 'number') &&
    typeof value.created_at_timestamp === 'number' &&
    (value.read_at_timestamp === null || typeof value.read_at_timestamp === 'number') &&
    value.type === NotificationType.RESERVATION_READY &&
    isRecord(value.payload)
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
  if (status === 403) return detail || 'Your account cannot use member notifications.'
  if (status === 404) return detail || 'The notification could not be found.'
  return detail || 'The library service could not load notifications. Please try again.'
}

async function request<T>(path: string, token: string, method: 'GET' | 'PATCH'): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new NotificationsApiError(0, 'Unable to reach the library service. Check that it is running and try again.')
  }
  const body = await readJson(response)
  if (!response.ok) throw new NotificationsApiError(response.status, errorMessage(response.status, body))
  return body as T
}

export async function listUnreadNotifications(token: string): Promise<Notification[]> {
  const body = await request<unknown>('/notifications?unread_only=true&limit=50', token, 'GET')
  if (!Array.isArray(body) || !body.every(isNotification)) {
    throw new NotificationsApiError(0, 'The library service returned an unexpected notifications response.')
  }
  return body
}

export async function markNotificationRead(token: string, notificationId: number): Promise<Notification> {
  const body = await request<unknown>(`/notifications/${notificationId}/read`, token, 'PATCH')
  if (!isNotification(body)) throw new NotificationsApiError(0, 'The library service returned an unexpected notification response.')
  return body
}
