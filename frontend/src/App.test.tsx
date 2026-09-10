import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { login } from './api/auth'
import { getBook, listBooks } from './api/books'
import { borrowBook, listBookLoans, listMyLoans, LoansApiError } from './api/loans'

vi.mock('./api/auth', () => ({ login: vi.fn() }))
vi.mock('./api/books', () => ({
  BooksApiError: class BooksApiError extends Error { status = 0 },
  listBooks: vi.fn(),
  getBook: vi.fn(),
  createBook: vi.fn(),
  updateBook: vi.fn(),
  deleteBook: vi.fn(),
}))
vi.mock('./api/loans', () => ({
  LoanStatus: { BORROWED: 1, RETURNED: 2 },
  LoansApiError: class LoansApiError extends Error { status: number; constructor(status: number, message: string) { super(message); this.status = status } },
  borrowBook: vi.fn(),
  listBookLoans: vi.fn(),
  listMyLoans: vi.fn(),
  returnLoan: vi.fn(),
}))

const loginMock = vi.mocked(login)
const listBooksMock = vi.mocked(listBooks)
const getBookMock = vi.mocked(getBook)
const listMyLoansMock = vi.mocked(listMyLoans)
const listBookLoansMock = vi.mocked(listBookLoans)
const borrowBookMock = vi.mocked(borrowBook)

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
    listMyLoansMock.mockResolvedValueOnce([])
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
    listMyLoansMock.mockResolvedValueOnce([])
    listBooksMock.mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    expect(await screen.findByRole('heading', { name: 'No books yet' })).toBeInTheDocument()
  })

  it('applies combined text and inclusive date filters', async () => {
    listBooksMock.mockResolvedValueOnce([]).mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    fireEvent.change(screen.getByLabelText('Search title or author'), { target: { value: 'Dune' } })
    fireEvent.change(screen.getByLabelText('Publication date from'), { target: { value: '2024-01-01' } })
    fireEvent.change(screen.getByLabelText('Publication date to'), { target: { value: '2024-01-31' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    await waitFor(() => expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {
      q: 'Dune', date_from: '2024-01-01T00:00:00Z', date_to: '2024-01-31T23:59:59Z',
    }))
    expect(screen.getByRole('heading', { name: 'No matching books' })).toBeInTheDocument()
  })

  it('rejects reversed dates without reloading and clears the active filters', async () => {
    listBooksMock.mockResolvedValueOnce([]).mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    fireEvent.change(screen.getByLabelText('Publication date from'), { target: { value: '2024-02-01' } })
    fireEvent.change(screen.getByLabelText('Publication date to'), { target: { value: '2024-01-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('start date must be on or before')
    expect(listBooksMock).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    await waitFor(() => expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {}))
    expect(screen.getByLabelText('Search title or author')).toHaveValue('')
  })

  it('formats the detail publication timestamp as an ISO calendar date', async () => {
    listMyLoansMock.mockResolvedValueOnce([])
    const book = { id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 2, available_copies: 1 }
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    render(<App />)
    await signIn('USER')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    expect(await screen.findByText('1970-01-01')).toBeInTheDocument()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('shows the backend loan conflict in an accessible popup', async () => {
    const book = { id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 1, available_copies: 1 }
    listMyLoansMock.mockResolvedValueOnce([])
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    const conflict = new LoansApiError(409, 'Active loan already exists')
    borrowBookMock.mockRejectedValueOnce(conflict)
    render(<App />)
    await signIn('USER')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Borrow book' }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('Active loan already exists')
  })

  it('lets an admin view loans for a book from the detail view', async () => {
    const book = { id: 1, title: 'Dune', author: 'Frank Herbert', date: 0, isbn: '9780441013593', loan_duration_days: 14, total_copies: 1, available_copies: 0 }
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    listBookLoansMock.mockResolvedValueOnce([{ id: 4, book_id: 1, user_id: 8, loan_timestamp: 100, due_at_timestamp: 200, returned_timestamp: null, status: 1 }])
    render(<App />)
    await signIn('ADMIN')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    fireEvent.click(await screen.findByRole('button', { name: 'View loan history' }))

    expect(await screen.findByRole('heading', { name: 'Loan history' })).toBeInTheDocument()
    expect(screen.getByText('Loan #4')).toBeInTheDocument()
    expect(listBookLoansMock).toHaveBeenCalledWith('header.eyJyb2xlIjoiQURNSU4ifQ==.signature', 1)
  })
})
