import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { login } from './api/auth'

vi.mock('./api/auth', () => ({ login: vi.fn() }))

const loginMock = vi.mocked(login)

describe('App', () => {
  it('announces client-side validation without sending a request', () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(loginMock).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent('Check the highlighted fields')
    expect(screen.getByText('Enter your username.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
  })

  it('keeps the username, clears the password, and focuses an API error', async () => {
    loginMock.mockResolvedValueOnce({ ok: false, message: 'Invalid username or password' })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Invalid username or password')
    expect(screen.getByLabelText('Username')).toHaveValue('alice')
    expect(screen.getByLabelText('Password')).toHaveValue('')
    await waitFor(() => expect(alert).toHaveFocus())
  })

  it('disables the form while a sign-in request is pending', () => {
    loginMock.mockReturnValueOnce(new Promise(() => {}))
    render(<App />)

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(screen.getByRole('button', { name: 'Signing in...' })).toBeDisabled()
    expect(loginMock).toHaveBeenCalledTimes(1)
  })

  it('shows signed-in state without rendering the access token and signs out', async () => {
    loginMock.mockResolvedValueOnce({ ok: true, accessToken: 'private-token' })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'You are signed in' })).toBeInTheDocument()
    expect(screen.queryByText('private-token')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })
})
