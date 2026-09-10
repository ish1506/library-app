import { afterEach, describe, expect, it, vi } from 'vitest'
import { login } from './auth'

describe('login', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('posts the API contract and returns a token on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: 'token', token_type: 'bearer' }), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(login({ username: 'alice', password: 'password' })).resolves.toEqual({
      ok: true,
      accessToken: 'token',
    })
    expect(fetchMock).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'alice', password: 'password' }),
    })
  })

  it('normalizes invalid credentials', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Invalid username or password' }), { status: 401 }),
    ))

    await expect(login({ username: 'alice', password: 'wrong' })).resolves.toEqual({
      ok: false,
      message: 'Invalid username or password',
    })
  })

  it('reports validation, network, and non-JSON failures safely', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: [] }), { status: 422 }),
    ))
    await expect(login({ username: 'alice', password: 'password' })).resolves.toMatchObject({
      ok: false,
      message: expect.stringContaining('invalid'),
    })

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(login({ username: 'alice', password: 'password' })).resolves.toMatchObject({
      ok: false,
      message: expect.stringContaining('Unable to reach'),
    })

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('failure', { status: 500 })))
    await expect(login({ username: 'alice', password: 'password' })).resolves.toMatchObject({
      ok: false,
      message: expect.stringContaining('could not complete'),
    })
  })
})
