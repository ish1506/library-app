import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { login } from './api/auth'
import { getBook, listBooks } from './api/books'

vi.mock('./api/auth', () => ({ login: vi.fn() }))
vi.mock('./api/books', () => ({
  BooksApiError: class BooksApiError extends Error { status = 0 },
  listBooks: vi.fn(),
  getBook: vi.fn(),
  createBook: vi.fn(),
  updateBook: vi.fn(),
  deleteBook: vi.fn(),
}))

const loginMock = vi.mocked(login)
const listBooksMock = vi.mocked(listBooks)
const getBookMock = vi.mocked(getBook)

function token(role: 'ADMIN' | 'USER') {
  return `header.${btoa(JSON.stringify({ role }))}.signature`
}

async function signIn(role: 'ADMIN' | 'USER') {
  loginMock.mockResolvedValueOnce({ ok: true, accessToken: token(role) })
  fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
  await screen.findByRole('heading', { name: 'Books' })
}

describe('App', () => {
  it('announces client-side login validation without sending a request', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(loginMock).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent('Check the highlighted fields')
    expect(screen.getByText('Enter your username.')).toBeInTheDocument()
  })

  it('loads a user catalogue without mutation controls', async () => {
    listBooksMock.mockResolvedValueOnce([{ id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 2, available_copies: 0 }])
    render(<App />)
    await signIn('USER')
    expect(await screen.findByRole('heading', { name: 'Dune' })).toBeInTheDocument()
    expect(screen.getByText('Currently unavailable')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Add book' })).not.toBeInTheDocument()
  })

  it('shows admin catalogue controls and signs out without rendering the token', async () => {
    listBooksMock.mockResolvedValueOnce([])
    render(<App />)
    await signIn('ADMIN')
    expect(screen.getByRole('button', { name: 'Add book' })).toBeInTheDocument()
    expect(screen.getByText('Administrator')).toBeInTheDocument()
    expect(screen.queryByText('header')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument())
  })

  it('handles an empty catalogue state', async () => {
    listBooksMock.mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    expect(await screen.findByRole('heading', { name: 'No books yet' })).toBeInTheDocument()
  })

  it('formats the detail publication timestamp as an ISO calendar date', async () => {
    const book = { id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 2, available_copies: 1 }
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    render(<App />)
    await signIn('USER')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    expect(await screen.findByText('1970-01-01')).toBeInTheDocument()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })
})
