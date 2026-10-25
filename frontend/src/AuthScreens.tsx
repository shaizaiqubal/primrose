import { useEffect, useState, type FormEvent } from 'react'
import { Mail } from 'lucide-react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Button, Field, Header } from './components/ui'
import {
  getApiError,
  registerAccount,
  sendVerificationEmail,
  signIn,
  verifyEmailOnce,
} from './authApi'

type InboxLocationState = {
  email?: string
  sendError?: string
}

function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell auth-shell">
      <Header />
      <main className="auth-page">{children}</main>
    </div>
  )
}

function PasswordField({
  label = 'Password',
  value,
  onChange,
}: {
  label?: string
  value: string
  onChange: (value: string) => void
}) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="field">
      <label className="field__label" htmlFor="password">{label}</label>
      <div className="password-field">
        <input
          autoComplete={label === 'Password' ? 'current-password' : 'new-password'}
          className="field__input"
          id="password"
          onChange={(event) => onChange(event.target.value)}
          placeholder="Your password"
          required
          type={visible ? 'text' : 'password'}
          value={value}
        />
        <button
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
          className="password-field__toggle"
          onClick={() => setVisible((current) => !current)}
          type="button"
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
    </div>
  )
}

export function SignInScreen() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const verified = (location.state as { verified?: boolean } | null)?.verified
  const signedIn = (location.state as { signedIn?: boolean } | null)?.signedIn

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const tokens = await signIn({ email, password })
      localStorage.setItem('primrose-access-token', tokens.access_token)
      localStorage.setItem('primrose-refresh-token', tokens.refresh_token)
      setPassword('')
      const returnTo = (location.state as { returnTo?: string } | null)?.returnTo
      navigate(returnTo?.startsWith('/') && !returnTo.startsWith('//') ? returnTo : '/', { replace: true })
    } catch (requestError) {
      const message = getApiError(requestError, 'We could not sign you in just now. Try again.')
      if (message.toLowerCase().includes('not verified')) {
        localStorage.setItem('primrose-pending-email', email)
        navigate('/inbox', { state: { email } })
      } else {
        setError(message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="auth-intro">
        <h1 className="auth-title">Welcome back.</h1>
        <p>Sign in to pick up where you left off.</p>
      </div>
      {verified && <p className="auth-notice" role="status">Your email is verified. Sign in to continue.</p>}
      {signedIn && <p className="auth-notice" role="status">You are signed in.</p>}
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <Field
          autoComplete="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />
        <PasswordField value={password} onChange={setPassword} />
        <Button className="auth-submit" disabled={submitting} type="submit" variant="primary">
          {submitting ? 'Signing in' : 'Sign in'}
        </Button>
      </form>
      <div className="auth-footnote">
        <span className="auth-unavailable" aria-disabled="true">Forgot your password?</span>
        <p>New to Primrose? <Link to="/signup">Create an account</Link></p>
      </div>
    </AuthLayout>
  )
}

export function SignUpScreen() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await registerAccount({ email, password })
      localStorage.setItem('primrose-pending-email', email)
      let sendError: string | undefined
      try {
        await sendVerificationEmail({ email })
      } catch (requestError) {
        sendError = getApiError(requestError, 'We could not send the verification email just now.')
      }
      navigate('/inbox', { replace: true, state: { email, sendError } satisfies InboxLocationState })
    } catch (requestError) {
      setError(getApiError(requestError, 'We could not create your account just now. Try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="auth-intro">
        <h1 className="auth-title">Create your account.</h1>
        <p>Save papers and add your own. We will email you a link to verify your address.</p>
      </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <Field
          autoComplete="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />
        <PasswordField label="Create a password" value={password} onChange={setPassword} />
        <Button className="auth-submit" disabled={submitting} type="submit" variant="primary">
          {submitting ? 'Creating account' : 'Create account'}
        </Button>
      </form>
      <div className="auth-footnote">
        <p>Already have an account? <Link to="/signin">Sign in</Link></p>
      </div>
    </AuthLayout>
  )
}

export function InboxScreen() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as InboxLocationState | null
  const [email, setEmail] = useState(
    state?.email ?? localStorage.getItem('primrose-pending-email') ?? '',
  )
  const [notice, setNotice] = useState('')
  const [error, setError] = useState(state?.sendError ?? '')
  const [sending, setSending] = useState(false)

  async function handleResend() {
    if (!email) {
      navigate('/signup', { replace: true })
      return
    }
    setSending(true)
    setError('')
    setNotice('')
    try {
      await sendVerificationEmail({ email })
      setNotice('A fresh verification link is on its way.')
    } catch (requestError) {
      setError(getApiError(requestError, 'We could not send the email just now. Try again.'))
    } finally {
      setSending(false)
    }
  }

  return (
    <AuthLayout>
      <div className="inbox-icon" aria-hidden="true"><Mail size={38} strokeWidth={1.6} /></div>
      <h1 className="auth-title">Check your inbox.</h1>
      {email ? (
        <p className="auth-copy">We sent a verification link to <strong>{email}</strong>. Open it to finish creating your account.</p>
      ) : (
        <p className="auth-copy">Enter your email and we will send a fresh verification link.</p>
      )}
      {!email && (
        <Field
          autoComplete="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />
      )}
      {error && <p className="auth-error" role="alert">{error}</p>}
      {notice && <p className="auth-notice" role="status">{notice}</p>}
      <div className="auth-actions">
        <Button disabled={sending} onClick={handleResend} type="button">
          {sending ? 'Sending' : 'Send it again'}
        </Button>
        <Link className="button button--ghost" onClick={() => localStorage.removeItem('primrose-pending-email')} to="/signup">
          Use a different email
        </Link>
      </div>
    </AuthLayout>
  )
}

export function VerifyEmailScreen() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setError('This verification link is missing its token. Request a new one from your inbox.')
      return
    }

    let active = true
    verifyEmailOnce(token)
      .then(() => {
        if (active) navigate('/', { replace: true })
      })
      .catch((requestError: unknown) => {
        if (active) setError(getApiError(requestError, 'We could not verify this link. Request a new one and try again.'))
      })

    return () => { active = false }
  }, [navigate, searchParams])

  return (
    <AuthLayout>
      <div className="auth-intro">
        <p className="eyebrow">Email verification</p>
        <h1 className="auth-title">{error ? 'This link needs attention.' : 'Verifying your email.'}</h1>
        <p role={error ? 'alert' : 'status'}>{error || 'Just a moment while we confirm your address.'}</p>
      </div>
      {error && <div className="auth-actions"><Link className="button button--primary" to="/inbox">Back to your inbox</Link></div>}
    </AuthLayout>
  )
}