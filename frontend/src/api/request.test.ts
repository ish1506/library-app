import { afterEach, describe, expect, it, vi } from 'vitest'
import { createRequest } from './request'

const request = createRequest(
  (status, body) => new Error(`${status}:${typeof body === 'object' ? 'body' : 'empty'}`),
)

describe('request', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('merges authorization, JSON content type, and request options', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      request<{ id: number }>('/books', 'token', {
        method: 'POST',
        body: JSON.stringify({ title: 'Dune' }),
        headers: { 'X-Request-Id': 'request-1' },
      }),
    ).resolves.toEqual({ id: 1 })

    expect(fetchMock).toHaveBeenCalledWith('/books', {
      method: 'POST',
      body: JSON.stringify({ title: 'Dune' }),
      headers: {
        Authorization: 'Bearer token',
        'Content-Type': 'application/json',
        'X-Request-Id': 'request-1',
      },
    })
  })

  it('returns undefined for an empty successful response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))

    await expect(
      request<undefined>('/books/1', 'token', { method: 'DELETE' }),
    ).resolves.toBeUndefined()
  })

  it('uses the supplied error factory for failed responses and network errors', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'No access' }), { status: 403 }))
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
    vi.stubGlobal('fetch', fetchMock)

    await expect(request('/books', 'token')).rejects.toThrow('403:body')
    await expect(request('/books', 'token')).rejects.toThrow('0:empty')
  })
})
