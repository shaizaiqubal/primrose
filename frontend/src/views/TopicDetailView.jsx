import { useParams } from "react-router-dom"

import EmptyState from "../components/EmptyState.jsx"
import ResultsList from "../components/ResultsList.jsx"
import useTopicDetail from "../hooks/useTopicDetail.js"

export default function TopicDetailView({
  onPaperSelect,
}) {
  const { topicId } = useParams()
  const { topic, loadingTopic, topicError, papers, loadingPapers, papersError } = useTopicDetail(topicId)
  const normalizedTopic = topic

  if (loadingTopic) {
    return (
      <div className="topic-detail-page">
        <div className="topic-detail-header">
          <div className="topic-detail-copy">
            <h1 className="home-heading">Research Topics</h1>
            <p className="home-sub">Loading topic…</p>
          </div>
        </div>
        <EmptyState message="Loading topic…" />
      </div>
    )
  }

  if (topicError) {
    return (
      <div className="topic-detail-page">
        <div className="topic-detail-header">
          <div className="topic-detail-copy">
            <h1 className="home-heading">Research Topics</h1>
            <p className="home-sub">{topicError}</p>
          </div>
        </div>
        <EmptyState message={topicError} />
      </div>
    )
  }

  if (!normalizedTopic) {
    return (
      <div className="topic-detail-page">
        <div className="topic-detail-header">
          <div className="topic-detail-copy">
            <h1 className="home-heading">Research Topics</h1>
            <p className="home-sub">Topic not found.</p>
          </div>
        </div>
        <EmptyState message="Topic not found." />
      </div>
    )
  }

  return (
    <div className="topic-detail-page">
      <div className="topic-detail-header">
        <div className="topic-detail-copy">
          <h1 className="home-heading">{normalizedTopic.name}</h1>
          <p className="home-sub">
            {normalizedTopic.paper_count} paper
            {normalizedTopic.paper_count === 1 ? "" : "s"} in this topic.
          </p>
        </div>
      </div>

      {loadingPapers && <EmptyState message="Loading papers…" />}

      {!loadingPapers && papersError && <EmptyState message={papersError} />}

      {!loadingPapers && !papersError && papers && papers.length > 0 && (
        <ResultsList
          docs={papers}
          label="Browse Papers"
          compact
          onSelect={(doc) => onPaperSelect(doc, { section: "topics", topicId })}
        />
      )}

      {!loadingPapers && !papersError && papers && papers.length === 0 && (
        <EmptyState message="No papers found for this topic." />
      )}
    </div>
  )
}
