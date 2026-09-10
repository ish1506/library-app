import { type FormEvent, useEffect, useRef, useState } from 'react'
import { login } from './api/auth'
import './App.css'

function App() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [isPending, setIsPending] = useState(false)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const errorSummary = useRef<HTMLDivElement>(null)

  const hasError = Boolean(usernameError || passwordError || requestError)

  useEffect(() => {
    if (hasError) errorSummary.current?.focus()
  }, [hasError])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isPending) return

    const nextUsernameError = username.trim() ? '' : 'Enter your username.'
    const nextPasswordError = password ? '' : 'Enter your password.'
    setUsernameError(nextUsernameError)
    setPasswordError(nextPasswordError)
    setRequestError('')

    if (nextUsernameError || nextPasswordError) return

    setIsPending(true)
    const result = await login({ username: username.trim(), password })
    setIsPending(false)

    if (result.ok) {
      setAccessToken(result.accessToken)
      setPassword('')
      return
    }

    setPassword('')
    setRequestError(result.message)
  }

  if (accessToken) {
    return (
      <main className="page">
        <section className="panel confirmation" aria-labelledby="signed-in-heading">
          <p className="eyebrow">Library</p>
          <h1 id="signed-in-heading">You are signed in</h1>
          <p>Your session is ready for the next library feature.</p>
          <button type="button" onClick={() => setAccessToken(null)}>
            Sign out
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="page">
      <section className="panel" aria-labelledby="login-heading">
        <p className="eyebrow">Library</p>
        <h1 id="login-heading">Sign in</h1>
        <p className="intro">Use your provisioned library account to continue.</p>

        {hasError && (
          <div className="error-summary" role="alert" tabIndex={-1} ref={errorSummary}>
            {requestError || 'Check the highlighted fields and try again.'}
          </div>
        )}
        {isPending && <p className="status" role="status">Signing in...</p>}

        <form onSubmit={handleSubmit} aria-busy={isPending} noValidate>
          <fieldset disabled={isPending}>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                aria-invalid={Boolean(usernameError)}
                aria-describedby={usernameError ? 'username-error' : undefined}
              />
              {usernameError && <p className="field-error" id="username-error">{usernameError}</p>}
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-invalid={Boolean(passwordError)}
                aria-describedby={passwordError ? 'password-error' : undefined}
              />
              {passwordError && <p className="field-error" id="password-error">{passwordError}</p>}
            </div>
            <button type="submit">{isPending ? 'Signing in...' : 'Sign in'}</button>
          </fieldset>
        </form>
      </section>
    </main>
  )
}

export default App
