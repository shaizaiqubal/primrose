import { LockKeyhole } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { Header } from './components/ui'

export function UnauthorizedScreen({ returnTo }: { returnTo?: string }) {
  const location = useLocation()
  const stateReturnTo = (location.state as { returnTo?: string } | null)?.returnTo
  const requestedPath = returnTo ?? stateReturnTo ?? '/'
  const destination = requestedPath.startsWith('/') && !requestedPath.startsWith('//') ? requestedPath : '/'
  const authState = { returnTo: destination }

  return (
    <div className="app-shell auth-shell">
      <Header />
      <main className="unauthorized-page">
        <LockKeyhole aria-hidden="true" className="unauthorized-page__icon" size={40} strokeWidth={1.6} />
        <div className="unauthorized-page__copy">
          <span className="eyebrow">Sign in required</span>
          <h1>Sign in to see this page.</h1>
          <p>This page belongs to your account. Sign in or create one, and we will bring you straight back here.</p>
        </div>
        <div className="unauthorized-page__actions">
          <Link className="button button--primary" to="/signin" state={authState}>Sign in</Link>
          <Link className="button button--ghost" to="/signup" state={authState}>Create account</Link>
        </div>
        <Link className="unauthorized-page__back" to="/">Back to search</Link>
      </main>
    </div>
  )
}