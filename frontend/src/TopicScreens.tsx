import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getApiErrorMessage, getTopic, getTopicPapers, getTopics, type Topic } from './api.ts'
import { PaperCard } from './components/PaperCard'
import { Button, Field, Header } from './components/ui'

type SortOrder = 'most' | 'fewest' | 'alphabetical'

export function TopicsScreen() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState<SortOrder>('most')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTopics()
      .then(setTopics)
      .catch((requestError: unknown) => setError(String(getApiErrorMessage(requestError, 'We could not load topics just now.'))))
      .finally(() => setLoading(false))
  }, [])

  const visibleTopics = useMemo(() => {
    const filtered = topics.filter((topic) => (topic.topic_name ?? '').toLowerCase().includes(filter.toLowerCase()))
    return [...filtered].sort((first, second) => {
      if (sort === 'fewest') return first.paper_count - second.paper_count
      if (sort === 'alphabetical') return (first.topic_name ?? '').localeCompare(second.topic_name ?? '')
      return second.paper_count - first.paper_count
    })
  }, [filter, sort, topics])

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} activePath="/topics" />
      <main className="browse-page">
        <header className="browse-heading">
          <h1>Topics</h1>
        </header>
        <div className="topic-controls">
          <Field label="Filter topics" onChange={(event) => setFilter(event.target.value)} placeholder="Type a word" value={filter} />
          <label className="field topic-sort">
            <span className="field__label">Sort by</span>
            <select className="field__input" onChange={(event) => setSort(event.target.value as SortOrder)} value={sort}>
              <option value="most">Most papers</option>
              <option value="fewest">Fewest papers</option>
              <option value="alphabetical">A to Z</option>
            </select>
          </label>
        </div>
        {loading && <div className="topic-rows" aria-busy="true">{[0, 1, 2, 3].map((key) => <div className="topic-row-skeleton" key={key} />)}</div>}
        {!loading && error && <StateCard title="Topics are unavailable just now." message="We could not reach Primrose. Try again in a moment." onRetry={() => { setLoading(true); setError(''); void getTopics().then(setTopics).catch(() => setError('We could not load topics just now.')).finally(() => setLoading(false)) }} />}
        {!loading && !error && visibleTopics.length === 0 && <p className="quiet-empty">No topics match that filter.</p>}
        {!loading && !error && visibleTopics.length > 0 && (
          <div className="topic-rows">
            {visibleTopics.map((topic) => (
              <Link className="topic-row" key={topic.topic_id} to={`/topics/${topic.topic_id}`}>
                <span>{topic.topic_name || 'Untitled topic'}</span>
                <span className="topic-row__count">{topic.paper_count} papers</span>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

function StateCard({ title, message, onRetry }: { title: string; message: string; onRetry: () => void }) {
  return (
    <div className="state-card" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
      <Button onClick={onRetry} variant="primary">Try again</Button>
    </div>
  )
}

export function TopicDetailScreen() {
  const { topicId } = useParams()
  const id = Number(topicId)
  const [topic, setTopic] = useState<Topic | null>(null)
  const [papers, setPapers] = useState<Awaited<ReturnType<typeof getTopicPapers>>>([])
  const [query, setQuery] = useState('')
  const [appliedQuery, setAppliedQuery] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const pageSize = 20

  useEffect(() => {
    if (!Number.isInteger(id) || id < 1) {
      setError('This topic could not be found.')
      setLoading(false)
      return
    }
    Promise.all([getTopic(id), getTopicPapers(id, undefined, 1, pageSize)])
      .then(([topicResponse, paperResponse]) => {
        setTopic(topicResponse)
        setPapers(paperResponse)
        setPage(1)
      })
      .catch((requestError: unknown) => setError(String(getApiErrorMessage(requestError, 'We could not load this topic just now.'))))
      .finally(() => setLoading(false))
  }, [id])

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setAppliedQuery(query.trim())
    setPage(1)
    try {
      const nextPapers = await getTopicPapers(id, query.trim() || undefined, 1, pageSize)
      setPapers(nextPapers)
    } catch (requestError) {
      setPapers([])
      setError(String(getApiErrorMessage(requestError, 'We could not search this topic just now.')))
    } finally {
      setLoading(false)
    }
  }

  async function showMore() {
    setLoadingMore(true)
    try {
      const nextPage = page + 1
      const nextPapers = await getTopicPapers(id, appliedQuery || undefined, nextPage, pageSize)
      setPapers((current) => [...current, ...nextPapers])
      setPage(nextPage)
    } catch (requestError) {
      setError(String(getApiErrorMessage(requestError, 'We could not load more papers just now.')))
    } finally {
      setLoadingMore(false)
    }
  }

  const hasMore = Boolean(topic && papers.length < topic.paper_count && papers.length >= page * pageSize)

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} activePath="/topics" />
      <main className="search-page topic-detail-page">
        <header className="topic-detail-heading">
          <Link className="back-link" to="/topics">Back to topics</Link>
          <h1>{topic?.topic_name ?? 'Topic'}</h1>
          {topic && <p>{topic.paper_count} papers in this topic.</p>}
        </header>
        <form className="search-form" onSubmit={submitSearch}>
          <label className="visually-hidden" htmlFor="topic-question">Ask within this topic</label>
          <input id="topic-question" onChange={(event) => setQuery(event.target.value)} placeholder="Ask within this topic" value={query} />
          <Button disabled={loading} type="submit" variant="primary">Search</Button>
        </form>
        {loading && <div className="search-results" aria-busy="true"><p className="search-results__status" role="status">Finding papers in this topic</p><div className="skeleton-card"><span className="skeleton-line" /><span className="skeleton-line skeleton-line--medium" /><span className="skeleton-line skeleton-line--meta" /></div></div>}
        {!loading && error && <StateCard title="We could not load these papers just now." message={error} onRetry={() => { setError(''); setLoading(true); void getTopicPapers(id, appliedQuery || undefined, 1, pageSize).then(setPapers).catch(() => setError('We could not load these papers just now.')).finally(() => setLoading(false)) }} />}
        {!loading && !error && papers.length === 0 && <div className="quiet-empty"><h2>No papers surfaced for that question.</h2><p>Try rephrasing it in a little more detail.</p></div>}
        {!loading && !error && papers.length > 0 && <section className="search-results"><p className="search-results__status">Papers in this topic</p>{papers.map((paper) => <PaperCard document={paper} key={paper.id} />)}</section>}
        {!error && topic && <div className="topic-pagination"><span>Showing {papers.length} of {topic.paper_count}</span>{hasMore && <Button disabled={loadingMore} onClick={showMore}>{loadingMore ? 'Loading papers' : 'Show more papers'}</Button>}</div>}
      </main>
    </div>
  )
}