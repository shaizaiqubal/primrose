import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getApiErrorMessage, getEntityPapers, listEntities, searchEntities, type Document, type Entity, type EntitySearchResult } from './api.ts'
import { PaperCard } from './components/PaperCard'
import { Button, Chip, Field, Header } from './components/ui'

type EntityType = 'method' | 'model' | 'dataset' | 'task' | 'metric'
type EntityTab = 'all' | EntityType
const tabs: { label: string; value: EntityTab }[] = [
  { label: 'All', value: 'all' },
  { label: 'Methods', value: 'method' },
  { label: 'Models', value: 'model' },
  { label: 'Datasets', value: 'dataset' },
  { label: 'Tasks', value: 'task' },
  { label: 'Metrics', value: 'metric' },
]

export function EntitiesScreen() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [searchResults, setSearchResults] = useState<EntitySearchResult[]>([])
  const [filter, setFilter] = useState('')
  const [tab, setTab] = useState<EntityTab>('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchLoading, setSearchLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const pageSize = 50

  async function loadEntities(nextPage: number, replace = false) {
    const response = await listEntities(tab === 'all' ? undefined : tab, nextPage, pageSize)
    setEntities((current) => replace ? response.items : [...current, ...response.items])
    setTotal(response.total)
    setPage(nextPage)
  }

  useEffect(() => {
    if (filter.trim()) return
    setLoading(true)
    setError('')
    void loadEntities(1, true)
      .catch((requestError: unknown) => setError(String(getApiErrorMessage(requestError, 'We could not load entities just now.'))))
      .finally(() => setLoading(false))
  }, [tab, filter])

  useEffect(() => {
    const query = filter.trim()
    if (!query) {
      setSearchResults([])
      setSearchLoading(false)
      return
    }

    const controller = new AbortController()
    setSearchLoading(true)
    setError('')
    const timeout = window.setTimeout(() => {
      searchEntities(query, 50, controller.signal)
        .then(setSearchResults)
        .catch((requestError: unknown) => {
          if (!controller.signal.aborted) {
            setSearchResults([])
            setError(String(getApiErrorMessage(requestError, 'We could not search entities just now.')))
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearchLoading(false)
        })
    }, 250)

    return () => {
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [filter])

  const visibleEntities = useMemo(() => {
    const source = filter.trim() ? searchResults : entities
    return tab === 'all' ? source : source.filter((entity) => entity.type.toLowerCase() === tab)
  }, [entities, filter, searchResults, tab])
  const grouped = tab === 'all'
    ? (['method', 'model', 'dataset', 'task', 'metric'] as const).map((type) => ({ type, items: visibleEntities.filter((entity) => entity.type.toLowerCase() === type) }))
    : [{ type: tab, items: visibleEntities }]

  const groupLabels: Record<EntityType, string> = {
    method: 'Methods',
    model: 'Models',
    dataset: 'Datasets',
    task: 'Tasks',
    metric: 'Metrics',
  }

  async function showMore() {
    if (filter.trim()) return
    setLoadingMore(true)
    setError('')
    try {
      await loadEntities(page + 1)
    } catch (requestError) {
      setError(String(getApiErrorMessage(requestError, 'We could not load more entities just now.')))
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} activePath="/entities" />
      <main className="entities-page">
        <div className="entities-heading">
          <div><h1>Entities</h1><p>The methods, tasks and ideas Primrose finds across the papers. Pick one to see every paper that mentions it.</p></div>
          <Field label="Filter entities" onChange={(event) => setFilter(event.target.value)} placeholder="Type a word" value={filter} />
        </div>
        <div className="entity-tabs" aria-label="Filter entity type" role="group">
          {tabs.map(({ label, value }) => <Chip key={value} onClick={() => setTab(value)} selected={tab === value}>{label}</Chip>)}
        </div>
        {(loading || searchLoading) && <div className="entity-groups" aria-busy="true"><p className="search-results__status" role="status">{searchLoading ? 'Searching entities' : 'Loading entities'}</p>{[0, 1, 2].map((key) => <div className="skeleton-card" key={key}><span className="skeleton-line skeleton-line--medium" /></div>)}</div>}
        {!loading && error && <div className="state-card" role="alert"><h2>Entities are unavailable just now.</h2><p>{error}</p><Button onClick={() => { setLoading(true); void loadEntities(1, true).catch(() => setError('We could not load entities just now.')).finally(() => setLoading(false)) }} variant="primary">Try again</Button></div>}
        {!loading && !searchLoading && !error && visibleEntities.length === 0 && <p className="quiet-empty">{filter.trim() ? 'No matching entities.' : 'No entities are available.'}</p>}
        {!loading && !searchLoading && !error && <div className="entity-groups">
          {grouped.filter((group) => group.items.length > 0).map((group) => (
            <section className="card entity-group" key={group.type}>
              <h2>{groupLabels[group.type as EntityType]}</h2>
              <div className="entity-group__chips">{group.items.map((entity) => <Link className="entity-chip-link" key={entity.id} to={`/entities/${entity.id}/papers`}><Chip>{entity.canonical_name}</Chip></Link>)}</div>
            </section>
          ))}
        </div>}
        {!loading && !searchLoading && !error && !filter.trim() && entities.length < total && <div className="entity-pagination"><span>Showing {entities.length} of {total}</span><Button disabled={loadingMore} onClick={showMore}>{loadingMore ? 'Loading entities' : 'Show more entities'}</Button></div>}
      </main>
    </div>
  )
}

export function EntityPapersScreen() {
  const { entityId } = useParams()
  const id = Number(entityId)
  const [entity, setEntity] = useState<Entity | null>(null)
  const [papers, setPapers] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!Number.isInteger(id) || id < 1) {
      setError('This entity could not be found.')
      setLoading(false)
      return
    }
    Promise.all([listEntities(undefined, 1, 100), getEntityPapers(id)])
      .then(([entityPage, documents]) => {
        setEntity(entityPage.items.find((item) => item.id === id) ?? null)
        setPapers(documents)
      })
      .catch((requestError: unknown) => setError(String(getApiErrorMessage(requestError, 'We could not load papers for this entity just now.'))))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} activePath="/entities" />
      <main className="search-page entity-papers-page">
        <Link className="back-link" to="/entities">Back to entities</Link>
        <header className="topic-detail-heading"><h1>{entity?.canonical_name ?? 'Entity papers'}</h1>{entity && <p>{entity.type[0].toUpperCase() + entity.type.slice(1)}</p>}</header>
        {loading && <div className="skeleton-card" aria-busy="true"><span className="skeleton-line" /><span className="skeleton-line skeleton-line--medium" /></div>}
        {!loading && error && <div className="state-card" role="alert"><h2>We could not load these papers.</h2><p>{error}</p></div>}
        {!loading && !error && papers.length === 0 && <p className="quiet-empty">No papers are currently connected to this entity.</p>}
        {!loading && !error && papers.length > 0 && <section className="search-results"><p className="search-results__status">Papers about this entity</p>{papers.map((paper) => <PaperCard document={paper} key={paper.id} />)}</section>}
      </main>
    </div>
  )
}