export type LoginCredentials = {
  username: string
  password: string
}

type TokenResponse = {
  access_token: string
  token_type?: string
}

type ApiError = {
  detail?: string
}

type ValidationError = {
  detail?: Array<{ loc: Array<string | number>; msg: string; type: string }>
}

export type LoginResult =
  | { ok: true; accessToken: string }
  | { ok: false; message: string }

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isTokenResponse(body: unknown): body is TokenResponse {
  return (
    typeof body === 'object' &&
    body !== null &&
    'access_token' in body &&
    typeof body.access_token === 'string' &&
    body.access_token.length > 0
  )
}

function isApiError(body: unknown): body is ApiError {
  return typeof body === 'object' && body !== null && 'detail' in body
}

function isValidationError(body: unknown): body is ValidationError {
  return isApiError(body) && Array.isArray(body.detail)
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

export async function login(credentials: LoginCredentials): Promise<LoginResult> {
  let response: Response

  try {
    response = await fetch(`${apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    })
  } catch {
    return { ok: false, message: 'Unable to reach the library service. Check that it is running and try again.' }
  }

  const body = await readJson(response)

  if (response.ok && isTokenResponse(body)) {
    return { ok: true, accessToken: body.access_token }
  }

  if (response.status === 401) {
    return {
      ok: false,
      message: isApiError(body) && typeof body.detail === 'string'
        ? body.detail
        : 'Invalid username or password',
    }
  }

  if (response.status === 422 && isValidationError(body)) {
    return { ok: false, message: 'The sign-in request was invalid. Check your details and try again.' }
  }

  return { ok: false, message: 'The library service could not complete your sign-in. Please try again.' }
}
