import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { login } from './api/auth'
import { getBook, listBooks } from './api/books'
import { borrowBook, listBookLoans, listMyLoans, LoansApiError } from './api/loans'
import { createReservation, listMyReservations } from './api/reservations'
import { listUnreadNotifications, markNotificationRead } from './api/notifications'

vi.mock('./api/auth', () => ({ login: vi.fn() }))
vi.mock('./api/books', () => ({
  BooksApiError: class BooksApiError extends Error {
    status = 0
  },
  listBooks: vi.fn(),
  getBook: vi.fn(),
  createBook: vi.fn(),
  updateBook: vi.fn(),
  deleteBook: vi.fn(),
}))
vi.mock('./api/loans', () => ({
  LoanStatus: { BORROWED: 1, RETURNED: 2 },
  LoansApiError: class LoansApiError extends Error {
    status: number
    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
  borrowBook: vi.fn(),
  listBookLoans: vi.fn(),
  listMyLoans: vi.fn(),
  returnLoan: vi.fn(),
}))
vi.mock('./api/reservations', () => ({
  ReservationStatus: { PENDING: 1, READY: 2, FULFILLED: 3, CANCELLED: 4, EXPIRED: 5 },
  ReservationsApiError: class ReservationsApiError extends Error {
    status: number
    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
  createReservation: vi.fn(),
  listMyReservations: vi.fn(),
  confirmReservation: vi.fn(),
  cancelReservation: vi.fn(),
}))
vi.mock('./api/notifications', () => ({
  NotificationType: { RESERVATION_READY: 1 },
  NotificationsApiError: class NotificationsApiError extends Error {
    status: number
    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
  listUnreadNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
}))

const loginMock = vi.mocked(login)
const listBooksMock = vi.mocked(listBooks)
const getBookMock = vi.mocked(getBook)
const listMyLoansMock = vi.mocked(listMyLoans)
const listBookLoansMock = vi.mocked(listBookLoans)
const borrowBookMock = vi.mocked(borrowBook)
const listMyReservationsMock = vi.mocked(listMyReservations)
const listUnreadNotificationsMock = vi.mocked(listUnreadNotifications)
const createReservationMock = vi.mocked(createReservation)
const markNotificationReadMock = vi.mocked(markNotificationRead)

beforeEach(() => {
  listMyReservationsMock.mockResolvedValue([])
  listUnreadNotificationsMock.mockResolvedValue([])
})

function token(role: 'ADMIN' | 'USER') {
  return `header.${btoa(JSON.stringify({ role }))}.signature`
}

async function signIn(role: 'ADMIN' | 'USER') {
  loginMock.mockResolvedValueOnce({ ok: true, accessToken: token(role) })
  fireEvent.change(screen.getByLabelText('Username'), {
    target: { value: 'alice' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'password' },
  })
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
    listBooksMock.mockResolvedValueOnce([
      {
        id: 1,
        title: 'Dune',
        author: 'Frank Herbert',
        date: 0,
        isbn: '9780441013593',
        loan_duration_days: 14,
        total_copies: 2,
        available_copies: 0,
        late_fee_cents_per_day: 50,
      },
    ])
    render(<App />)
    await signIn('USER')
    expect(await screen.findByRole('heading', { name: 'Dune' })).toBeInTheDocument()
    expect(screen.getByText('Currently unavailable')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Add book' })).not.toBeInTheDocument()
  })

  it('navigates from the user loans page back to the catalogue', async () => {
    listMyLoansMock.mockResolvedValue([])
    listBooksMock.mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')

    fireEvent.click(screen.getByRole('button', { name: 'My loans' }))
    expect(await screen.findByRole('heading', { name: 'My loans' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Back to catalogue' }))

    expect(await screen.findByRole('heading', { name: 'Catalogue' })).toBeInTheDocument()
  })

  it('shows admin catalogue controls and signs out without rendering the token', async () => {
    listBooksMock.mockResolvedValueOnce([])
    render(<App />)
    await signIn('ADMIN')
    expect(screen.getByRole('button', { name: 'Add book' })).toBeInTheDocument()
    expect(screen.getByText('Administrator')).toBeInTheDocument()
    expect(screen.queryByText('header')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument(),
    )
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
    fireEvent.change(screen.getByLabelText('Search title or author'), {
      target: { value: 'Dune' },
    })
    fireEvent.change(screen.getByLabelText('Publication date from'), {
      target: { value: '2024-01-01' },
    })
    fireEvent.change(screen.getByLabelText('Publication date to'), {
      target: { value: '2024-01-31' },
    })
    fireEvent.change(screen.getByLabelText('Sort catalogue'), { target: { value: 'author:desc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    await waitFor(() =>
      expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {
        q: 'Dune',
        date_from: '2024-01-01T00:00:00Z',
        date_to: '2024-01-31T23:59:59Z',
        sort_by: 'author',
        sort_order: 'desc',
      }),
    )
    expect(screen.getByRole('heading', { name: 'No matching books' })).toBeInTheDocument()
  })

  it('keeps the default sort out of the list request and resets an applied sort', async () => {
    listBooksMock.mockResolvedValue([])
    render(<App />)
    await signIn('USER')

    expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {})
    fireEvent.change(screen.getByLabelText('Sort catalogue'), { target: { value: 'title:asc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    await waitFor(() =>
      expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {
        sort_by: 'title',
        sort_order: 'asc',
      }),
    )
    expect(screen.getByText(/sorted by title a-z/)).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Clear filters' })[0])
    await waitFor(() =>
      expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {}),
    )
    expect(screen.getByLabelText('Sort catalogue')).toHaveValue('')
  })

  it('preserves applied sorting when retrying a failed catalogue request', async () => {
    listBooksMock
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error('temporary failure'))
      .mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    fireEvent.change(screen.getByLabelText('Sort catalogue'), { target: { value: 'date:desc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('temporary failure')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() =>
      expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {
        sort_by: 'date',
        sort_order: 'desc',
      }),
    )
  })

  it('rejects reversed dates without reloading and clears the active filters', async () => {
    listBooksMock.mockResolvedValueOnce([]).mockResolvedValueOnce([])
    render(<App />)
    await signIn('USER')
    fireEvent.change(screen.getByLabelText('Publication date from'), {
      target: { value: '2024-02-01' },
    })
    fireEvent.change(screen.getByLabelText('Publication date to'), {
      target: { value: '2024-01-01' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('start date must be on or before')
    expect(listBooksMock).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    await waitFor(() =>
      expect(listBooksMock).toHaveBeenLastCalledWith('header.eyJyb2xlIjoiVVNFUiJ9.signature', {}),
    )
    expect(screen.getByLabelText('Search title or author')).toHaveValue('')
  })

  it('formats the detail publication timestamp as an ISO calendar date', async () => {
    listMyLoansMock.mockResolvedValueOnce([])
    const book = {
      id: 1,
      title: 'Dune',
      author: 'Frank Herbert',
      date: 0,
      isbn: '9780441013593',
      loan_duration_days: 14,
      total_copies: 2,
      available_copies: 1,
      late_fee_cents_per_day: 50,
    }
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    render(<App />)
    await signIn('USER')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    expect(await screen.findByText('1970-01-01')).toBeInTheDocument()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('shows the backend loan conflict in an accessible popup', async () => {
    const book = {
      id: 1,
      title: 'Dune',
      author: 'Frank Herbert',
      date: 0,
      isbn: '9780441013593',
      loan_duration_days: 14,
      total_copies: 1,
      available_copies: 1,
      late_fee_cents_per_day: 50,
    }
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

  it('lets a user reserve an unavailable title', async () => {
    const book = {
      id: 1,
      title: 'Dune',
      author: 'Frank Herbert',
      date: 0,
      isbn: '9780441013593',
      loan_duration_days: 14,
      total_copies: 1,
      available_copies: 0,
      late_fee_cents_per_day: 50,
    }
    listBooksMock.mockResolvedValue(book ? [book] : [])
    getBookMock.mockResolvedValue(book)
    createReservationMock.mockResolvedValue({
      id: 3,
      book_id: 1,
      user_id: 7,
      created_at_timestamp: 100,
      ready_at_timestamp: null,
      expires_at_timestamp: null,
      fulfilled_at_timestamp: null,
      cancelled_at_timestamp: null,
      status: 1,
    })
    render(<App />)
    await signIn('USER')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Reserve book' }))
    await waitFor(() =>
      expect(createReservationMock).toHaveBeenCalledWith(
        'header.eyJyb2xlIjoiVVNFUiJ9.signature',
        1,
      ),
    )
    expect(await screen.findByRole('status')).toHaveTextContent('Reservation created')
  })

  it('shows unread notifications and marks them read', async () => {
    const notification = {
      id: 5,
      user_id: 7,
      reservation_id: 3,
      created_at_timestamp: 100,
      read_at_timestamp: null,
      type: 1 as const,
      payload: { title: 'Dune', author: 'Frank Herbert', expires_at_timestamp: 200 },
    }
    listBooksMock.mockResolvedValueOnce([])
    listUnreadNotificationsMock.mockResolvedValueOnce([notification])
    markNotificationReadMock.mockResolvedValueOnce({ ...notification, read_at_timestamp: 300 })
    render(<App />)
    await signIn('USER')
    fireEvent.click(screen.getByRole('button', { name: 'Notifications (1)' }))
    expect(screen.getByText('Dune is ready')).toBeInTheDocument()
    expect(screen.getByText(/Hold until/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mark read' }))
    await waitFor(() =>
      expect(markNotificationReadMock).toHaveBeenCalledWith(
        'header.eyJyb2xlIjoiVVNFUiJ9.signature',
        5,
      ),
    )
  })

  it('lets an admin view loans for a book from the detail view', async () => {
    const book = {
      id: 1,
      title: 'Dune',
      author: 'Frank Herbert',
      date: 0,
      isbn: '9780441013593',
      loan_duration_days: 14,
      total_copies: 1,
      available_copies: 0,
      late_fee_cents_per_day: 50,
    }
    listBooksMock.mockResolvedValueOnce([book])
    getBookMock.mockResolvedValueOnce(book)
    listBookLoansMock.mockResolvedValueOnce([
      {
        id: 4,
        book_id: 1,
        user_id: 8,
        loan_timestamp: 100,
        due_at_timestamp: 200,
        returned_timestamp: null,
        status: 1,
        late_fee_cents: 0,
      },
    ])
    render(<App />)
    await signIn('ADMIN')
    fireEvent.click(await screen.findByRole('button', { name: 'View details' }))
    fireEvent.click(await screen.findByRole('button', { name: 'View loan history' }))

    expect(await screen.findByRole('heading', { name: 'Loan history' })).toBeInTheDocument()
    expect(screen.getByText('Loan #4')).toBeInTheDocument()
    expect(listBookLoansMock).toHaveBeenCalledWith('header.eyJyb2xlIjoiQURNSU4ifQ==.signature', 1)
  })
})
