const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export type ApiErrorFactory = (status: number, body: unknown) => Error

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

export function createRequest(errorFactory: ApiErrorFactory) {
  return async function request<T>(
    path: string,
    token: string,
    init: RequestInit = {},
  ): Promise<T> {
    let response: Response
    try {
      response = await fetch(`${apiBaseUrl}${path}`, {
        ...init,
        headers: {
          Authorization: `Bearer ${token}`,
          ...(init.body ? { 'Content-Type': 'application/json' } : {}),
          ...init.headers,
        },
      })
    } catch {
      throw errorFactory(0, undefined)
    }

    const body = response.status === 204 ? undefined : await readJson(response)
    if (!response.ok) throw errorFactory(response.status, body)
    return body as T
  }
}
