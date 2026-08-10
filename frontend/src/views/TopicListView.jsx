import { useMemo, useState } from "react"

import EmptyState from "../components/EmptyState.jsx"
import TopicCard from "../components/TopicCard.jsx"
import useTopics from "../hooks/useTopics.js"
import { normalizeTopic, topicId } from "../utils/topics.js"

export default function TopicListView({ onTopicClick }) {
  const { topics, loading, error } = useTopics()
  const [query, setQuery] = useState("")
  const [sortValue, setSortValue] = useState("paper-count-desc")

  const filteredTopics = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    const base = (topics ?? []).map(normalizeTopic)

    const filtered = normalizedQuery
      ? base.filter((topic) => topic.name.toLowerCase().includes(normalizedQuery))
      : base

    const sorted = [...filtered].sort((a, b) => {
      if (sortValue === "paper-count-asc") {
        const countDiff = (a.paper_count ?? 0) - (b.paper_count ?? 0)
        if (countDiff !== 0) return countDiff
        return a.name.localeCompare(b.name)
      }

      if (sortValue === "alphabetical") {
        return a.name.localeCompare(b.name)
      }

      const countDiff = (b.paper_count ?? 0) - (a.paper_count ?? 0)
      if (countDiff !== 0) return countDiff

      return a.name.localeCompare(b.name)
    })

    return sorted
  }, [query, sortValue, topics])

  const topicCount = topics?.length ?? 0
  const paperCount = (topics ?? []).reduce((sum, topic) => sum + (topic.paper_count ?? 0), 0)

  return (
    <div className="topic-page">
      <div className="topic-page-header">
        <div>
          <h1 className="home-heading">Research Topics</h1>
          <p className="home-sub">
            Explore the research themes discovered automatically across the corpus.
          </p>
        </div>

        <div className="topic-summary">
          <div className="topic-summary-item">
            <span className="topic-summary-value">{topicCount}</span>
            <span className="topic-summary-label">Topics</span>
          </div>
          <div className="topic-summary-item">
            <span className="topic-summary-value">{paperCount}</span>
            <span className="topic-summary-label">Papers</span>
          </div>
        </div>
      </div>

      <div className="topic-controls">
        <div className="topic-search-field">
          <label className="topic-controls-label" htmlFor="topic-search-input">
            Search topics
          </label>
          <input
            id="topic-search-input"
            className="topic-search-input"
            type="search"
            placeholder="Search topics..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <div className="topic-sort-field">
          <label className="topic-controls-label" htmlFor="topic-sort-select">
            Sort
          </label>
          <select
            id="topic-sort-select"
            className="topic-sort-select"
            value={sortValue}
            onChange={(event) => setSortValue(event.target.value)}
          >
            <option value="paper-count-desc">Paper Count (Most to least)</option>
            <option value="paper-count-asc">Paper Count (Least to most)</option>
            <option value="alphabetical">A-Z</option>
          </select>
        </div>
      </div>

      {loading && <EmptyState message="Loading topics…" />}

      {!loading && error && <EmptyState message={error} />}

      {!loading && !error && filteredTopics.length === 0 && (
        <EmptyState message="No topics match your search." />
      )}

      {!loading && !error && filteredTopics.length > 0 && (
        <div className="topic-card-list">
          {filteredTopics.map((topic) => (
            <TopicCard
              key={topicId(topic)}
              topic={topic}
              onClick={onTopicClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}
