import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Header } from './components/ui'

export function NotFoundScreen() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized) return
    navigate('/', { state: { query: normalized } })
  }

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} />
      <main className="not-found-page">
        <div className="not-found-copy">
          <p className="eyebrow">404 / Page not found</p>
          <h1>This page is not here.</h1>
          <p>The link may be old or mistyped. Nothing is wrong with your account or your library. Try asking for what you were after.</p>
        </div>
        <form className="not-found-search" onSubmit={handleSearch}>
          <label className="field__label" htmlFor="not-found-query">Search instead</label>
          <div className="search-form">
            <input id="not-found-query" onChange={(event) => setQuery(event.target.value)} placeholder="Describe what you are looking for" value={query} />
            <Button type="submit" variant="primary">Search</Button>
          </div>
        </form>
        <nav className="not-found-nav" aria-label="Suggested destinations">
          <span>Or go to</span>
          <Link className="button button--ghost" to="/topics">Topics</Link>
          <Link className="button button--ghost" to="/entities">Entities</Link>
          <Link className="button button--ghost" to="/library">Your library</Link>
        </nav>
      </main>
    </div>
  )
}