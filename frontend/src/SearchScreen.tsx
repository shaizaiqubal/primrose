import { useEffect, useRef, useState, type FormEvent } from 'react'
import { CircleAlert } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { getApiErrorMessage, getDocuments, getCorpora, searchDocuments, type Document, type RankedDocument } from './api.ts'
import { PaperCard } from './components/PaperCard'
import { Button, Header } from './components/ui'

const BROWSE_PAGE_SIZE = 20

function isUnauthorized(error: unknown) {
  return typeof error === 'object' && error !== null && 'response' in error && (error as { response?: { status?: number } }).response?.status === 401
}

function SearchSkeleton({ status = 'Finding papers closest in meaning' }: { status?: string }) {
  return (
    <div className="search-results search-results--loading" aria-busy="true">
      <p className="search-results__status" role="status">{status}</p>
      {[0, 1].map((key) => (
        <article className="skeleton-card" aria-hidden="true" key={key}>
          <span className="skeleton-line skeleton-line--short" />
          <span className="skeleton-line" />
          <span className="skeleton-line skeleton-line--medium" />
          <span className="skeleton-line skeleton-line--meta" />
          <div className="skeleton-actions"><span /><span /></div>
        </article>
      ))}
    </div>
  )
}

export function SearchScreen() {
  const location = useLocation()
  const initialQuery = (location.state as { query?: string } | null)?.query ?? ''
  const [query, setQuery] = useState(initialQuery)
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [results, setResults] = useState<RankedDocument[]>([])
  const [browsePapers, setBrowsePapers] = useState<Document[]>([])
  const [browsePage, setBrowsePage] = useState(1)
  const [browseLoading, setBrowseLoading] = useState(true)
  const [browseError, setBrowseError] = useState(false)
  const [browseMoreError, setBrowseMoreError] = useState(false)
  const [browseLoadingMore, setBrowseLoadingMore] = useState(false)
  const [browseHasMore, setBrowseHasMore] = useState(false)
  const signedIn = Boolean(localStorage.getItem('primrose-access-token'))
  const [corpusState, setCorpusState] = useState<'public' | 'checking' | 'available' | 'empty' | 'error'>(signedIn ? 'checking' : 'public')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const checkingCorpus = corpusState === 'checking'

  useEffect(() => {
    if (!signedIn || !checkingCorpus) return
    getCorpora()
      .then((corpora) => setCorpusState(corpora.length > 0 ? 'available' : 'empty'))
      .catch((requestError) => {
        if (isUnauthorized(requestError)) {
          localStorage.removeItem('primrose-access-token')
          localStorage.removeItem('primrose-refresh-token')
          setCorpusState('public')
        } else {
          setCorpusState('error')
        }
      })
  }, [checkingCorpus, signedIn])

  useEffect(() => {
    if (corpusState === 'checking' || corpusState === 'empty' || corpusState === 'error') return
    getDocuments(1, BROWSE_PAGE_SIZE)
      .then((documents) => {
        setBrowsePapers(documents)
        setBrowseHasMore(documents.length === BROWSE_PAGE_SIZE)
      })
      .catch(() => setBrowseError(true))
      .finally(() => setBrowseLoading(false))
  }, [corpusState])

  async function runSearch(searchTerm: string) {
    if (corpusState === 'empty' || corpusState === 'checking') return
    const normalizedQuery = searchTerm.trim()
    if (!normalizedQuery) {
      inputRef.current?.focus()
      return
    }
    setSubmittedQuery(normalizedQuery)
    setLoading(true)
    setError('')
    try {
      setResults(await searchDocuments(normalizedQuery))
    } catch (requestError) {
      setResults([])
      setError(await getApiErrorMessage(requestError, 'We could not reach Primrose just now.'))
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runSearch(query)
  }

  async function showMorePapers() {
    if (browseLoadingMore || !browseHasMore) return
    setBrowseLoadingMore(true)
    setBrowseMoreError(false)
    try {
      const nextPage = browsePage + 1
      const nextPapers = await getDocuments(nextPage, BROWSE_PAGE_SIZE)
      setBrowsePapers((current) => [...current, ...nextPapers])
      setBrowsePage(nextPage)
      setBrowseHasMore(nextPapers.length === BROWSE_PAGE_SIZE)
    } catch {
      setBrowseMoreError(true)
    } finally {
      setBrowseLoadingMore(false)
    }
  }

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} />
      <main className="search-page">
        <section className="search-prompt" aria-labelledby="search-heading">
          <h1 id="search-heading">Ask in your own words.</h1>
          <form className="search-form" onSubmit={handleSubmit}>
            <label className="visually-hidden" htmlFor="research-question">Research question</label>
            <input
              autoComplete="off"
              id="research-question"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Describe what you are trying to understand"
              ref={inputRef}
              value={query}
            />
            <Button disabled={loading || checkingCorpus || corpusState === 'empty'} type="submit" variant="primary">
              {loading ? 'Searching' : 'Search'}
            </Button>
          </form>
        </section>

        {loading && <SearchSkeleton />}
        {corpusState === 'empty' && !loading && (
          <div className="search-empty search-empty--corpus">
            <h2>Your corpus is waiting to be built.</h2>
            <p>Create a corpus before searching. It gives Primrose the papers to work from.</p>
            <Link className="button button--primary" to="/corpora/new">Create corpus</Link>
          </div>
        )}
        {corpusState === 'error' && !loading && (
          <div className="search-error" role="alert">
            <CircleAlert aria-hidden="true" size={32} strokeWidth={1.6} />
            <h2>We could not check your corpus just now.</h2>
            <p>Your search is ready whenever you are. Try again in a moment.</p>
            <Button onClick={() => setCorpusState('checking')} variant="primary">Try again</Button>
          </div>
        )}
        {corpusState !== 'empty' && corpusState !== 'error' && !loading && !submittedQuery && browseLoading && <SearchSkeleton status="Loading papers to explore" />}
        {corpusState !== 'empty' && corpusState !== 'error' && !loading && !submittedQuery && browseError && (
          <div className="search-error" role="alert">
            <CircleAlert aria-hidden="true" size={32} strokeWidth={1.6} />
            <h2>We could not load papers just now.</h2>
            <p>Your search is ready whenever you are. Try again in a moment.</p>
            <Button onClick={() => {
              setBrowseLoading(true)
              setBrowseError(false)
              getDocuments(1, BROWSE_PAGE_SIZE)
                .then((documents) => {
                  setBrowsePapers(documents)
                  setBrowseHasMore(documents.length === BROWSE_PAGE_SIZE)
                  setBrowsePage(1)
                })
                .catch(() => setBrowseError(true))
                .finally(() => setBrowseLoading(false))
            }} variant="primary">Try again</Button>
          </div>
        )}
        {!loading && error && (
          <div className="search-error" role="alert">
            <CircleAlert aria-hidden="true" size={32} strokeWidth={1.6} />
            <h2>We could not reach Primrose just now.</h2>
            <p>Your question is still in the box. Check your connection, then try again.</p>
            <div className="sample-row">
              <Button onClick={() => void runSearch(submittedQuery)} variant="primary">Try again</Button>
              <Button onClick={() => inputRef.current?.focus()}>Edit question</Button>
            </div>
          </div>
        )}
        {!loading && corpusState !== 'empty' && !error && submittedQuery && results.length === 0 && (
          <div className="search-empty">
            <h2>No papers surfaced for that question.</h2>
            <p>Try rephrasing it in a little more detail.</p>
          </div>
        )}
        {!loading && results.length > 0 && (
          <section className="search-results" aria-label="Search results">
            <p className="search-results__status">Papers closest in meaning</p>
            {results.map(({ document }) => <PaperCard document={document} key={document.id} />)}
          </section>
        )}
        {!loading && corpusState !== 'empty' && corpusState !== 'error' && !submittedQuery && !browseLoading && !browseError && browsePapers.length > 0 && (
          <section className="search-results" aria-label="Papers in the collection">
            <p className="search-results__status">Papers</p>
            {browsePapers.map((document) => <PaperCard document={document} key={document.id} />)}
            {browseMoreError && <p className="paper-card__error" role="alert">Could not load more papers. Try again.</p>}
            {browseHasMore && (
              <div className="topic-pagination">
                <span>{browsePapers.length} papers shown</span>
                <Button disabled={browseLoadingMore} onClick={() => void showMorePapers()}>
                  {browseLoadingMore ? 'Loading papers' : browseMoreError ? 'Try again' : 'Show more papers'}
                </Button>
              </div>
            )}
          </section>
        )}

        <nav className="search-browse" aria-label="Browse Primrose">
          <span>Prefer to browse?</span>
          <Link to="/topics">Topics</Link>
          <span aria-hidden="true">·</span>
          <Link to="/entities">Entities</Link>
        </nav>
      </main>
    </div>
  )
}
