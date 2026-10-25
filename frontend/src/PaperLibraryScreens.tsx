import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Bookmark, LogOut, Minus, Plus, X } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  api,
  createDocument,
  deleteDocument,
  getApiErrorMessage,
  getDocument,
  getDocumentEntities,
  getMyBookmarks,
  getMyUploads,
  getRelatedDocuments,
  getRecommendedPapers,
  logout,
  removeBookmark,
  type Document,
  type Entity,
  type RankedDocument,
  type RecommendedPaper,
} from './api.ts'
import { Button, Chip, Field, Header } from './components/ui'
import { UnauthorizedScreen } from './UnauthorizedScreen'

function byline(authors: string | null, year: number | null) {
  const names = authors?.split(',').map((name) => name.trim()).filter(Boolean) ?? []
  const authorText = names.length > 4 ? `${names.slice(0, 2).join(', ')} and ${names.length - 2} others` : names.join(', ')
  return [authorText, year].filter(Boolean).join(', ')
}

export function PaperScreen() {
  const { paperId } = useParams()
  const id = Number(paperId)
  const navigate = useNavigate()
  const [paper, setPaper] = useState<Document | null>(null)
  const [related, setRelated] = useState<RankedDocument[]>([])
  const [entities, setEntities] = useState<Entity[]>([])
  const [saved, setSaved] = useState(false)
  const [journey, setJourney] = useState<RecommendedPaper[] | null>(null)
  const [journeyOpen, setJourneyOpen] = useState(false)
  const [journeyLoading, setJourneyLoading] = useState(false)
  const [journeyError, setJourneyError] = useState('')
  const journeyController = useRef<AbortController | null>(null)
  const [abstractSize, setAbstractSize] = useState(() => Number(localStorage.getItem('primrose-abstract-size')) || 16)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!Number.isInteger(id) || id < 1) {
      setError('This paper could not be found.')
      setLoading(false)
      return
    }
    const requests = [getDocument(id), getDocumentEntities(id), getRelatedDocuments(id)] as const
    Promise.all(requests)
      .then(([document, paperEntities, relatedPapers]) => {
        setPaper(document)
        setEntities(paperEntities)
        setRelated(relatedPapers)
      })
      .catch((requestError: unknown) => setError(String(getApiErrorMessage(requestError, 'We could not load this paper just now.'))))
      .finally(() => setLoading(false))

    if (localStorage.getItem('primrose-access-token')) {
      void getMyBookmarks().then((bookmarks) => setSaved(bookmarks.some((item) => item.id === id))).catch(() => undefined)
    }
  }, [id])

  function changeAbstractSize(delta: number) {
    const nextSize = Math.min(22, Math.max(14, abstractSize + delta))
    setAbstractSize(nextSize)
    localStorage.setItem('primrose-abstract-size', String(nextSize))
  }

  async function generateJourney() {
    journeyController.current?.abort()
    const controller = new AbortController()
    journeyController.current = controller
    setJourneyLoading(true)
    setJourneyError('')
    try {
      setJourney(await getRecommendedPapers(id, controller.signal))
      setJourneyOpen(true)
    } catch (requestError) {
      if (!controller.signal.aborted) setJourneyError(String(getApiErrorMessage(requestError, 'We could not build a journey. Nothing was changed.')))
    } finally {
      if (!controller.signal.aborted) setJourneyLoading(false)
    }
  }

  function cancelJourney() {
    journeyController.current?.abort()
    journeyController.current = null
    setJourneyLoading(false)
  }

  async function toggleBookmark() {
    if (!paper) return
    if (!localStorage.getItem('primrose-access-token')) {
      navigate('/unauthorized', { state: { returnTo: `/papers/${paper.id}` } })
      return
    }
    try {
      if (saved) await removeBookmark(paper.id)
      else await api.post(`/documents/${paper.id}/bookmark`)
      setSaved(!saved)
    } catch {
      setError('We could not update this saved paper just now.')
    }
  }

  const entityTypeOrder = ['method', 'model', 'dataset', 'task', 'metric']
  const entityTypes = [...new Set(entities.map((entity) => entity.type.trim()).filter(Boolean))].sort((first, second) => {
    const firstIndex = entityTypeOrder.indexOf(first.toLowerCase())
    const secondIndex = entityTypeOrder.indexOf(second.toLowerCase())
    if (firstIndex === -1 && secondIndex === -1) return first.localeCompare(second)
    if (firstIndex === -1) return 1
    if (secondIndex === -1) return -1
    return firstIndex - secondIndex
  })

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} />
      {loading ? <main className="paper-layout"><div className="skeleton-card"><span className="skeleton-line" /><span className="skeleton-line skeleton-line--medium" /></div></main> : error || !paper ? (
        <main className="browse-page"><div className="state-card" role="alert"><h2>We could not open this paper.</h2><p>{error || 'This paper could not be found.'}</p><Link className="button button--primary" to="/">Back to search</Link></div></main>
      ) : (
        <main className="paper-layout">
          <aside className="related-rail" aria-labelledby="related-heading">
            <h2 id="related-heading">Related papers</h2>
            {related.length === 0 && <p className="muted-copy">No related papers are available yet.</p>}
            {related.map(({ document: relatedPaper }) => (
              <Link className="related-link" key={relatedPaper.id} to={`/papers/${relatedPaper.id}`}>
                <span>{relatedPaper.title}</span>
                <small>{byline(relatedPaper.authors, relatedPaper.year_published)}</small>
              </Link>
            ))}
          </aside>

          <article className="paper-reading">
            <Link className="back-link" onClick={() => navigate(-1)} to="/">Back to results</Link>
            <p className="paper-reading__meta">{byline(paper.authors, paper.year_published)}</p>
            <h1>{paper.title}</h1>
            <div className="paper-reading__actions">
              {paper.url && <a className="button button--primary" href={paper.url} rel="noreferrer" target="_blank">View full paper</a>}
              <Button aria-label={saved ? 'Saved. Remove from saved' : 'Save for later'} onClick={() => void toggleBookmark()} title={saved ? 'Saved. Remove from saved' : 'Save for later'} variant="icon">
                <Bookmark fill={saved ? 'currentColor' : 'none'} size={19} />
              </Button>
              <span className="paper-reading__spacer" />
              <Button aria-label="Smaller text" onClick={() => changeAbstractSize(-1)} title="Smaller text" variant="icon"><Minus size={17} /></Button>
              <Button aria-label="Larger text" onClick={() => changeAbstractSize(1)} title="Larger text" variant="icon"><Plus size={17} /></Button>
            </div>
            <p className="paper-reading__abstract" style={{ fontSize: `${abstractSize}px` }}>{paper.abstract}</p>
            {journeyOpen && journey && (
              <section className="reading-journey" aria-labelledby="journey-heading">
                <div className="reading-journey__heading">
                  <div><h2 id="journey-heading">Reading journey</h2><p>A suggested order, starting here.</p></div>
                  <Button onClick={() => setJourneyOpen(false)}>Hide journey</Button>
                </div>
                {journey.map((step) => (
                  <article className="journey-step" key={`${step.position}-${step.id}`}>
                    <span className="journey-step__number">{step.position}</span>
                    <div><p className="journey-step__meta">{byline(step.authors, step.year_published)}</p><h3><Link to={`/papers/${step.id}`}>{step.title}</Link></h3><p className="journey-step__note">{step.recommendation_note}</p></div>
                  </article>
                ))}
              </section>
            )}
          </article>

          <aside className="paper-side-rail">
            <section className="card entity-panel">
              <div>
                <h2>Entities</h2>
                <p>The methods, tasks and ideas this paper is about. Select one to find more papers.</p>
              </div>
              {entityTypes.map((type) => {
                const matching = entities.filter((entity) => entity.type.trim().toLowerCase() === type.toLowerCase())
                return <div className="entity-panel__group" key={type}>
                  <h3>{type[0].toUpperCase() + type.slice(1)}</h3>
                  <div className="entity-panel__chips">{matching.map((entity) => <Chip key={entity.id} onClick={() => navigate(`/entities/${entity.id}/papers`)}>{entity.canonical_name}</Chip>)}</div>
                </div>
              })}
              {entities.length === 0 && <p className="muted-copy">No extracted entities are available for this paper.</p>}
              {entities[0] && <Link className="accent-link" to={`/entities/${entities[0].id}/papers`}>Find papers about {entities[0].canonical_name}</Link>}
            </section>
            {journeyOpen ? (
              <section className="card journey-prompt"><div><h2>Journey is open</h2><span>Shown below the abstract</span></div><Button onClick={() => setJourneyOpen(false)}>Hide</Button></section>
            ) : journeyLoading ? (
              <section className="card journey-loading" aria-busy="true"><div><h2>Building your reading journey</h2><span>Finding a useful order to read</span></div><div className="journey-skeletons"><span /><span /><span /></div><Button onClick={cancelJourney}>Cancel</Button></section>
            ) : journeyError ? (
              <section className="card journey-error" role="alert"><h2>We could not build a journey.</h2><p>Nothing was changed.</p><div className="sample-row"><Button onClick={() => void generateJourney()} variant="primary">Try again</Button><Button onClick={() => setJourneyError('')}>Dismiss</Button></div></section>
            ) : (
              <section className="card journey-prompt"><div><h2>Not sure what next?</h2><span>Optional reading journey</span></div><Button onClick={() => void generateJourney()}>Generate</Button></section>
            )}
          </aside>
        </main>
      )}
    </div>
  )
}

export function LibraryScreen() {
  const navigate = useNavigate()
  const [saved, setSaved] = useState<Document[]>([])
  const [uploads, setUploads] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)

  async function loadLibrary() {
    setLoading(true)
    setError('')
    try {
      const [savedPapers, uploadedPapers] = await Promise.all([getMyBookmarks(), getMyUploads()])
      setSaved(savedPapers)
      setUploads(uploadedPapers)
    } catch (requestError) {
      setError(String(getApiErrorMessage(requestError, 'We could not load your library just now.')))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!localStorage.getItem('primrose-access-token')) {
      return
    }
    void loadLibrary()
  }, [navigate])

  async function removeSaved(id: number) {
    try {
      await removeBookmark(id)
      setSaved((current) => current.filter((paper) => paper.id !== id))
    } catch {
      setError('We could not remove that saved paper just now.')
    }
  }

  async function removeUpload(id: number) {
    try {
      await deleteDocument(id)
      setUploads((current) => current.filter((paper) => paper.id !== id))
    } catch {
      setError('We could not remove that uploaded paper just now.')
    }
  }

  function handleAdded(paper: Document) {
    setUploads((current) => [paper, ...current])
    setDrawerOpen(false)
  }

  if (!localStorage.getItem('primrose-access-token')) {
    return <UnauthorizedScreen returnTo="/library" />
  }

  async function handleLogout() {
    const refreshToken = localStorage.getItem('primrose-refresh-token')
    try {
      await logout(refreshToken)
    } catch {
      // Clear the local session even when the API is unavailable.
    } finally {
      localStorage.removeItem('primrose-access-token')
      localStorage.removeItem('primrose-refresh-token')
      navigate('/', { replace: true })
    }
  }

  return (
    <div className="app-shell">
      <Header authenticated activePath="/library" />
      <main className="library-page">
        <header className="browse-heading"><h1>Your library</h1><p>Papers you saved and papers you added yourself.</p></header>
        {error && <p className="auth-error" role="alert">{error}</p>}
        {loading ? <div className="library-columns" aria-busy="true"><div className="skeleton-card" /><div className="skeleton-card" /></div> : (
          <div className="library-columns">
            <LibraryColumn title="Saved" papers={saved} emptyTitle="Nothing saved yet" emptyMessage="Save a paper from your search results or a paper page and it will wait for you here." emptyAction={<Link className="button button--ghost" to="/">Start a search</Link>} onRemove={removeSaved} />
            <LibraryColumn title="Uploaded" papers={uploads} emptyTitle="No papers added yet" emptyMessage="Add a paper of your own with its title and abstract, and it will show up here." emptyAction={<Button onClick={() => setDrawerOpen(true)} variant="primary">Add a paper</Button>} onRemove={removeUpload} action={<Button onClick={() => setDrawerOpen(true)} variant="primary">Add a paper</Button>} />
          </div>
        )}
      </main>
      {drawerOpen && <AddPaperDrawer onClose={() => setDrawerOpen(false)} onCreated={handleAdded} />}
      <Button className="library-logout" onClick={() => void handleLogout()} title="Log out">
        <LogOut aria-hidden="true" size={16} />
        Log out
      </Button>
    </div>
  )
}

function LibraryColumn({
  title,
  papers,
  emptyTitle,
  emptyMessage,
  emptyAction,
  onRemove,
  action,
}: {
  title: string
  papers: Document[]
  emptyTitle: string
  emptyMessage: string
  emptyAction: React.ReactNode
  onRemove: (id: number) => void
  action?: React.ReactNode
}) {
  return (
    <section className="library-column">
      <div className="library-column__heading"><h2>{title}</h2>{action}</div>
      {papers.length === 0 ? <div className="library-empty">
        <Bookmark aria-hidden="true" size={36} strokeWidth={1.6} />
        <h3>{emptyTitle}</h3>
        <p>{emptyMessage}</p>
        {emptyAction}
      </div> : papers.map((paper) => <div className="library-row" key={paper.id}>
        <Link className="library-row__link" to={`/papers/${paper.id}`}>
          <span className="library-row__meta">{byline(paper.authors, paper.year_published)}</span>
          <span className="library-row__title">{paper.title}</span>
        </Link>
        <Button className="library-row__remove" onClick={() => onRemove(paper.id)}>Remove</Button>
      </div>)}
    </section>
  )
}

function AddPaperDrawer({ onClose, onCreated }: { onClose: () => void; onCreated: (paper: Document) => void }) {
  const [title, setTitle] = useState('')
  const [abstract, setAbstract] = useState('')
  const [authors, setAuthors] = useState('')
  const [year, setYear] = useState('')
  const [arxivId, setArxivId] = useState('')
  const [url, setUrl] = useState('')
  const [categories, setCategories] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  const yearValue = useMemo(() => year === '' ? null : Number(year), [year])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = [
      !title.trim() ? 'Add a title.' : '',
      !abstract.trim() ? 'Add an abstract.' : '',
      year && !/^\d+$/.test(year) ? 'Year must contain digits only.' : '',
    ].filter(Boolean)
    setErrors(validationErrors)
    if (validationErrors.length) return
    setSubmitting(true)
    try {
      const created = await createDocument({
        title: title.trim(),
        abstract: abstract.trim(),
        authors: authors.trim() || null,
        year_published: yearValue,
        arxiv_id: arxivId.trim() || null,
        url: url.trim() || null,
        categories: categories.trim() || null,
      })
      onCreated(created)
    } catch (requestError) {
      setErrors([String(getApiErrorMessage(requestError, 'We could not add this paper just now.'))])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section aria-labelledby="add-paper-heading" aria-modal="true" className="paper-drawer" role="dialog">
        <div className="paper-drawer__heading"><h2 id="add-paper-heading">Add a paper</h2><Button aria-label="Close" onClick={onClose} title="Close" variant="icon"><X size={20} /></Button></div>
        <form className="paper-drawer__form" onSubmit={handleSubmit}>
          {errors.length > 0 && <div className="auth-error" role="alert">{errors.map((message) => <p key={message}>{message}</p>)}</div>}
          <Field label="Title" requirement="Required" onChange={(event) => setTitle(event.target.value)} placeholder="Paper title" required value={title} />
          <label className="field"><span className="field__label">Abstract <span className="field__requirement">Required</span></span><textarea className="field__input field__textarea" onChange={(event) => setAbstract(event.target.value)} placeholder="Paste the abstract" required value={abstract} /></label>
          <Field label="Authors" requirement="Optional" onChange={(event) => setAuthors(event.target.value)} placeholder="Names separated by commas" value={authors} />
          <div className="form-grid-two">
            <Field inputMode="numeric" label="Year" requirement="Optional" onChange={(event) => setYear(event.target.value)} placeholder="2020" value={year} />
            <Field label="arXiv ID" requirement="Optional" onChange={(event) => setArxivId(event.target.value)} placeholder="" value={arxivId} />
          </div>
          <div className="form-grid-two">
            <Field autoComplete="url" label="Link" requirement="Optional" onChange={(event) => setUrl(event.target.value)} placeholder="https://" type="url" value={url} />
            <Field label="Categories" requirement="Optional" onChange={(event) => setCategories(event.target.value)} placeholder="cs.CL" value={categories} />
          </div>
          <div className="paper-drawer__actions"><Button disabled={submitting} type="submit" variant="primary">{submitting ? 'Adding paper' : 'Add paper'}</Button><Button onClick={onClose} type="button">Cancel</Button></div>
        </form>
      </section>
    </div>
  )
}