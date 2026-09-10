import { type FormEvent, useEffect, useRef, useState } from 'react'
import { login } from './api/auth'
import { debugLog } from './debug'
import {
  BooksApiError,
  createBook,
  deleteBook,
  getBook,
  listBooks,
  type Book,
  type BookCreate,
  updateBook,
} from './api/books'
import { borrowBook, listMyLoans, LoansApiError, LoanStatus, returnLoan, type BookLoan } from './api/loans'
import './App.css'

type Role = 'ADMIN' | 'USER'
type Session = { accessToken: string; role: Role }
type View = 'list' | 'detail' | 'loans' | 'form'
type FormValues = {
  title: string
  author: string
  date: string
  isbn: string
  loan_duration_days: string
  total_copies: string
}

const emptyForm: FormValues = {
  title: '', author: '', date: '', isbn: '', loan_duration_days: '', total_copies: '',
}

function decodeRole(token: string): Role | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return decoded.role === 'ADMIN' || decoded.role === 'USER' ? decoded.role : null
  } catch {
    return null
  }
}

function dateForApi(value: string): string {
  return `${value}T00:00:00Z`
}

function formatPublicationDate(timestamp: number): string {
  return new Date(timestamp * 1000).toISOString().slice(0, 10)
}

function formatLoanDate(timestamp: number): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp * 1000))
}

function formFromBook(book: Book): FormValues {
  return {
    title: book.title,
    author: book.author,
    date: '',
    isbn: book.isbn,
    loan_duration_days: String(book.loan_duration_days),
    total_copies: String(book.total_copies),
  }
}

function availability(book: Book): { label: string; available: boolean } {
  return book.available_copies > 0
    ? { label: `${book.available_copies} available`, available: true }
    : { label: 'Currently unavailable', available: false }
}

function App() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [isPending, setIsPending] = useState(false)
  const [session, setSession] = useState<Session | null>(null)
  const [view, setView] = useState<View>('list')
  const [books, setBooks] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [formValues, setFormValues] = useState(emptyForm)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [loans, setLoans] = useState<BookLoan[]>([])
  const [loanLoading, setLoanLoading] = useState(false)
  const [loanError, setLoanError] = useState('')
  const [loanPendingId, setLoanPendingId] = useState<number | null>(null)
  const [borrowPending, setBorrowPending] = useState(false)
  const [borrowMessage, setBorrowMessage] = useState('')
  const [loanPopupMessage, setLoanPopupMessage] = useState('')
  const [currentTimestamp] = useState(() => Date.now() / 1000)
  const errorSummary = useRef<HTMLDivElement>(null)
  const loginHasError = Boolean(usernameError || passwordError || requestError)

  useEffect(() => {
    if (loginHasError) errorSummary.current?.focus()
  }, [loginHasError])

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isPending) return
    const nextUsernameError = username.trim() ? '' : 'Enter your username.'
    const nextPasswordError = password ? '' : 'Enter your password.'
    setUsernameError(nextUsernameError)
    setPasswordError(nextPasswordError)
    setRequestError('')
    if (nextUsernameError || nextPasswordError) return

    setIsPending(true)
    try {
      const result = await login({ username: username.trim(), password })
      setPassword('')
      if (!result.ok) {
        setRequestError(result.message)
        return
      }
      const role = decodeRole(result.accessToken)
      if (!role) {
        setRequestError('The library service returned an invalid sign-in response. Please try again.')
        return
      }
      const nextSession = { accessToken: result.accessToken, role }
      setSession(nextSession)
      setRequestError('')
      setView('list')
      void refreshBooks(nextSession)
      if (role === 'USER') void refreshLoans(nextSession)
    } catch {
      debugLog('login_unexpected_error')
      setPassword('')
      setRequestError('The library service could not complete your sign-in. Please try again.')
    } finally {
      setIsPending(false)
    }
  }

  function signOut(message = '') {
    setSession(null)
    setBooks([])
    setSelectedBook(null)
    setView('list')
    setDeleteConfirm(false)
    setLoans([])
    setLoanError('')
    setBorrowMessage('')
    setLoanPopupMessage('')
    setRequestError(message)
  }

  async function refreshBooks(currentSession = session) {
    if (!currentSession) return
    setListLoading(true)
    setListError('')
    try {
      setBooks(await listBooks(currentSession.accessToken))
    } catch (error) {
      if (error instanceof BooksApiError && error.status === 401) signOut(error.message)
      else setListError(error instanceof Error ? error.message : 'Unable to load the catalogue.')
    } finally {
      setListLoading(false)
    }
  }

  async function refreshLoans(currentSession = session) {
    if (!currentSession || currentSession.role !== 'USER') return
    setLoanLoading(true)
    setLoanError('')
    try {
      setLoans(await listMyLoans(currentSession.accessToken))
    } catch (error) {
      if (error instanceof LoansApiError && error.status === 401) signOut(error.message)
      else {
        const message = error instanceof Error ? error.message : 'Unable to load your loans.'
        setLoanError(message)
        setLoanPopupMessage(message)
      }
    } finally {
      setLoanLoading(false)
    }
  }

  async function openDetail(id: number) {
    if (!session) return
    setView('detail')
    setDetailLoading(true)
    setDetailError('')
    setBorrowMessage('')
    setSelectedBook(null)
    try {
      setSelectedBook(await getBook(session.accessToken, id))
    } catch (error) {
      if (error instanceof BooksApiError && error.status === 401) signOut(error.message)
      else setDetailError(error instanceof Error ? error.message : 'Unable to load that book.')
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleBorrow() {
    if (!session || session.role !== 'USER' || !selectedBook || borrowPending || selectedBook.available_copies <= 0) return
    setBorrowPending(true)
    setBorrowMessage('')
    setDetailError('')
    try {
      const loan = await borrowBook(session.accessToken, selectedBook.id)
      await Promise.all([refreshBooks(session), refreshLoans(session), openDetail(selectedBook.id)])
      setBorrowMessage(`Borrowed successfully. Due ${formatLoanDate(loan.due_at_timestamp)}.`)
    } catch (error) {
      if (error instanceof LoansApiError && error.status === 401) signOut(error.message)
      else {
        const message = error instanceof Error ? error.message : 'Unable to borrow this book.'
        setDetailError(message)
        setLoanPopupMessage(message)
        if (error instanceof LoansApiError && error.status === 409) {
          await Promise.all([refreshBooks(session), openDetail(selectedBook.id)])
        }
      }
    } finally {
      setBorrowPending(false)
    }
  }

  async function handleReturn(loan: BookLoan) {
    if (!session || session.role !== 'USER' || loanPendingId !== null) return
    setLoanPendingId(loan.id)
    setLoanError('')
    try {
      await returnLoan(session.accessToken, loan.id)
      await Promise.all([refreshLoans(session), refreshBooks(session)])
    } catch (error) {
      if (error instanceof LoansApiError && error.status === 401) signOut(error.message)
      else {
        const message = error instanceof Error ? error.message : 'Unable to return this loan.'
        setLoanError(message)
        setLoanPopupMessage(message)
      }
    } finally {
      setLoanPendingId(null)
    }
  }

  function openCreate() {
    setSelectedBook(null)
    setFormValues(emptyForm)
    setFormErrors({})
    setRequestError('')
    setView('form')
  }

  function openEdit() {
    if (!selectedBook) return
    setFormValues(formFromBook(selectedBook))
    setFormErrors({})
    setRequestError('')
    setView('form')
  }

  function validateForm(isEdit: boolean) {
    const errors: Record<string, string> = {}
    if (!formValues.title.trim()) errors.title = 'Enter a title.'
    if (!formValues.author.trim()) errors.author = 'Enter an author.'
    if (!isEdit && !formValues.date) errors.date = 'Enter a publication date.'
    if (!formValues.isbn.trim()) errors.isbn = 'Enter an ISBN.'
    const loanDays = Number(formValues.loan_duration_days)
    const copies = Number(formValues.total_copies)
    if (!Number.isInteger(loanDays) || loanDays < 1) errors.loan_duration_days = 'Enter at least 1 day.'
    if (!Number.isInteger(copies) || copies < 0) errors.total_copies = 'Enter zero or more copies.'
    setFormErrors(errors)
    return errors
  }

  async function handleBookSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!session || isPending) return
    const isEdit = Boolean(selectedBook)
    if (Object.keys(validateForm(isEdit)).length) return
    setIsPending(true)
    setRequestError('')
    const values = {
      title: formValues.title.trim(),
      author: formValues.author.trim(),
      isbn: formValues.isbn.trim(),
      loan_duration_days: Number(formValues.loan_duration_days),
      total_copies: Number(formValues.total_copies),
    }
    try {
      if (selectedBook) {
        const sparseChanges: Partial<BookCreate> = {}
        const current = selectedBook
        if (values.title !== current.title) sparseChanges.title = values.title
        if (values.author !== current.author) sparseChanges.author = values.author
        if (values.isbn !== current.isbn) sparseChanges.isbn = values.isbn
        if (values.loan_duration_days !== current.loan_duration_days) sparseChanges.loan_duration_days = values.loan_duration_days
        if (values.total_copies !== current.total_copies) sparseChanges.total_copies = values.total_copies
        if (formValues.date) sparseChanges.date = dateForApi(formValues.date)
        await updateBook(session.accessToken, selectedBook.id, sparseChanges)
      } else {
        await createBook(session.accessToken, { ...values, date: dateForApi(formValues.date) })
      }
      setView('list')
      await refreshBooks(session)
    } catch (error) {
      if (error instanceof BooksApiError && error.status === 401) signOut(error.message)
      else setRequestError(error instanceof Error ? error.message : 'Unable to save the book.')
    } finally {
      setIsPending(false)
    }
  }

  async function handleDelete() {
    if (!session || !selectedBook || isPending) return
    setIsPending(true)
    setRequestError('')
    try {
      await deleteBook(session.accessToken, selectedBook.id)
      setDeleteConfirm(false)
      setView('list')
      await refreshBooks(session)
    } catch (error) {
      if (error instanceof BooksApiError && error.status === 401) signOut(error.message)
      else setRequestError(error instanceof Error ? error.message : 'Unable to delete the book.')
    } finally {
      setIsPending(false)
    }
  }

  if (!session) {
    return (
      <main className="page"><section className="panel" aria-labelledby="login-heading">
        <p className="eyebrow">Library</p><h1 id="login-heading">Sign in</h1>
        <p className="intro">Use your provisioned library account to continue.</p>
        {loginHasError && <div className="error-summary" role="alert" tabIndex={-1} ref={errorSummary}>{requestError || 'Check the highlighted fields and try again.'}</div>}
        {isPending && <p className="status" role="status">Signing in...</p>}
        <form onSubmit={handleLogin} aria-busy={isPending} noValidate><fieldset disabled={isPending}>
          <div className="field"><label htmlFor="username">Username</label><input id="username" name="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} aria-invalid={Boolean(usernameError)} aria-describedby={usernameError ? 'username-error' : undefined} />{usernameError && <p className="field-error" id="username-error">{usernameError}</p>}</div>
          <div className="field"><label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(passwordError)} aria-describedby={passwordError ? 'password-error' : undefined} />{passwordError && <p className="field-error" id="password-error">{passwordError}</p>}</div>
          <button type="submit">{isPending ? 'Signing in...' : 'Sign in'}</button>
        </fieldset></form>
      </section></main>
    )
  }

  const currentRole = session.role
  return <main className="app-shell">
    <header className="app-header"><div><p className="eyebrow">Library catalogue</p><h1>Books</h1></div><div className="header-actions"><span className="role-label">{currentRole === 'ADMIN' ? 'Administrator' : 'Member'}</span>{currentRole === 'USER' && <button className="button-secondary" type="button" onClick={() => { setView('loans'); void refreshLoans() }}>My loans</button>}<button className="button-secondary" type="button" onClick={() => signOut()}>Sign out</button></div></header>
    {requestError && <div className="error-summary" role="alert" tabIndex={-1}>{requestError}</div>}
    {view === 'list' && <section aria-labelledby="catalogue-heading"><div className="section-heading"><div><h2 id="catalogue-heading">Catalogue</h2><p className="muted">Browse the library collection and check availability.</p></div>{currentRole === 'ADMIN' && <button type="button" onClick={openCreate}>Add book</button>}</div>
      {listLoading && <p className="status" role="status">Loading catalogue...</p>}
      {listError && <div className="error-summary" role="alert">{listError}<button type="button" className="button-secondary" onClick={() => void refreshBooks()}>Retry</button></div>}
      {!listLoading && !listError && books.length === 0 && <div className="empty-state"><h3>No books yet</h3><p>The catalogue is empty.</p></div>}
      {!listLoading && !listError && books.length > 0 && <div className="book-list" role="list">{books.map((book) => { const state = availability(book); return <article className="book-card" role="listitem" key={book.id}><div><h3>{book.title}</h3><p>{book.author}</p><span className={`availability ${state.available ? 'available' : 'unavailable'}`}>{state.label}</span></div><button className="button-secondary" type="button" onClick={() => void openDetail(book.id)}>View details</button></article> })}</div>}
    </section>}
     {view === 'detail' && <section aria-labelledby="detail-heading"><button className="back-button" type="button" onClick={() => setView('list')}>Back to catalogue</button>{detailLoading && <p className="status" role="status">Loading book...</p>}{detailError && <div className="error-summary" role="alert">{detailError}</div>}{borrowMessage && <p className="success-message" role="status">{borrowMessage}</p>}{selectedBook && <><div className="detail-heading"><div><p className="eyebrow">Book details</p><h2 id="detail-heading">{selectedBook.title}</h2><p className="muted">{selectedBook.author}</p></div>{currentRole === 'ADMIN' && <div className="inline-actions"><button type="button" onClick={openEdit}>Edit</button><button className="button-danger" type="button" onClick={() => setDeleteConfirm(true)}>Delete</button></div>}{currentRole === 'USER' && <button type="button" onClick={() => void handleBorrow()} disabled={borrowPending || selectedBook.available_copies <= 0}>{borrowPending ? 'Borrowing...' : 'Borrow book'}</button>}</div><dl className="metadata"><div><dt>ISBN</dt><dd>{selectedBook.isbn}</dd></div><div><dt>Publication date</dt><dd>{formatPublicationDate(selectedBook.date)}</dd></div><div><dt>Loan duration</dt><dd>{selectedBook.loan_duration_days} days</dd></div><div><dt>Total copies</dt><dd>{selectedBook.total_copies}</dd></div><div><dt>Availability</dt><dd>{availability(selectedBook).label}</dd></div></dl></>}
     </section>}
     {view === 'loans' && currentRole === 'USER' && <section aria-labelledby="loans-heading"><div className="section-heading"><div><p className="eyebrow">Member circulation</p><h2 id="loans-heading">My loans</h2><p className="muted">Keep track of books you currently have borrowed.</p></div><button className="button-secondary" type="button" onClick={() => void refreshLoans()} disabled={loanLoading}>Refresh</button></div>{loanLoading && <p className="status" role="status">Loading your loans...</p>}{loanError && <div className="error-summary" role="alert">{loanError}<button type="button" className="button-secondary" onClick={() => void refreshLoans()}>Retry</button></div>}{!loanLoading && !loanError && loans.length === 0 && <div className="empty-state"><h3>No active loans</h3><p>Books you borrow will appear here.</p></div>}{!loanLoading && !loanError && loans.length > 0 && <div className="loan-list" role="list">{loans.map((loan) => { const book = books.find((item) => item.id === loan.book_id); const overdue = loan.status === LoanStatus.BORROWED && loan.due_at_timestamp < currentTimestamp; return <article className="loan-card" role="listitem" key={loan.id}><div><h3>{book?.title ?? `Book #${loan.book_id}`}</h3><p className="muted">{book?.author ?? 'Title details are not available in the current catalogue.'}</p><dl className="loan-meta"><div><dt>Borrowed</dt><dd>{formatLoanDate(loan.loan_timestamp)}</dd></div><div><dt>Due</dt><dd>{formatLoanDate(loan.due_at_timestamp)}</dd></div></dl>{overdue && <span className="availability overdue">Overdue</span>}</div><button type="button" onClick={() => void handleReturn(loan)} disabled={loanPendingId !== null}>{loanPendingId === loan.id ? 'Returning...' : 'Return book'}</button></article> })}</div>}</section>}
     {view === 'form' && currentRole === 'ADMIN' && <section aria-labelledby="form-heading"><button className="back-button" type="button" onClick={() => setView(selectedBook ? 'detail' : 'list')}>Cancel</button><div className="section-heading"><div><p className="eyebrow">{selectedBook ? 'Edit book' : 'New book'}</p><h2 id="form-heading">{selectedBook ? 'Update book' : 'Add a book'}</h2></div></div>{selectedBook && <p className="muted">Leave publication date blank to keep the existing date ({formatPublicationDate(selectedBook.date)}).</p>}{requestError && <div className="error-summary" role="alert">{requestError}</div>}<form onSubmit={handleBookSubmit} noValidate aria-busy={isPending}><fieldset disabled={isPending}><div className="form-grid">{(['title', 'author', 'date', 'isbn'] as const).map((field) => <div className="field" key={field}><label htmlFor={field}>{field === 'date' ? 'Publication date' : field === 'isbn' ? 'ISBN' : field[0].toUpperCase() + field.slice(1)}</label><input id={field} type={field === 'date' ? 'date' : 'text'} value={formValues[field]} onChange={(event) => setFormValues({ ...formValues, [field]: event.target.value })} required={!selectedBook || field !== 'date'} aria-invalid={Boolean(formErrors[field])} aria-describedby={formErrors[field] ? `${field}-error` : undefined} />{formErrors[field] && <p className="field-error" id={`${field}-error`}>{formErrors[field]}</p>}</div>)}<div className="field"><label htmlFor="loan_duration_days">Loan duration (days)</label><input id="loan_duration_days" type="number" min="1" step="1" value={formValues.loan_duration_days} onChange={(event) => setFormValues({ ...formValues, loan_duration_days: event.target.value })} aria-invalid={Boolean(formErrors.loan_duration_days)} />{formErrors.loan_duration_days && <p className="field-error">{formErrors.loan_duration_days}</p>}</div><div className="field"><label htmlFor="total_copies">Total copies</label><input id="total_copies" type="number" min="0" step="1" value={formValues.total_copies} onChange={(event) => setFormValues({ ...formValues, total_copies: event.target.value })} aria-invalid={Boolean(formErrors.total_copies)} />{formErrors.total_copies && <p className="field-error">{formErrors.total_copies}</p>}</div></div><button type="submit">{isPending ? 'Saving...' : selectedBook ? 'Save changes' : 'Create book'}</button></fieldset></form></section>}
     {deleteConfirm && <div className="dialog-backdrop"><div className="dialog" role="dialog" aria-modal="true" aria-labelledby="delete-heading"><h2 id="delete-heading">Delete this book?</h2><p>This will permanently remove {selectedBook?.title} from the catalogue.</p><div className="inline-actions"><button className="button-secondary" type="button" onClick={() => setDeleteConfirm(false)} disabled={isPending}>Cancel</button><button className="button-danger" type="button" onClick={() => void handleDelete()} disabled={isPending}>{isPending ? 'Deleting...' : 'Delete book'}</button></div></div></div>}
     {loanPopupMessage && <div className="dialog-backdrop"><div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="loan-error-heading" aria-describedby="loan-error-message"><p className="eyebrow">Loan request</p><h2 id="loan-error-heading">Unable to complete request</h2><p id="loan-error-message">{loanPopupMessage}</p><button type="button" autoFocus onClick={() => setLoanPopupMessage('')}>Close</button></div></div>}
   </main>
}

export default App
