import { useEffect } from "react"
import { useParams } from "react-router-dom"

import EmptyState from "../components/EmptyState.jsx"
import ResultsList from "../components/ResultsList.jsx"
import RecommendationPanel from "../components/RecommendationPanel.jsx"
import usePaperById from "../hooks/usePaperById.js"
import usePaperDetail from "../hooks/usePaperDetail.js"
import { formatDocumentMeta } from "../utils/formatDocumentMeta.js"

export default function PaperView({
  onPaperSelect,
}) {
  const { paperId } = useParams()
  const { paper, loading, error } = usePaperById(paperId)
  const meta = formatDocumentMeta(paper)
  const {
    related,
    loadingRelated,
    recommended,
    loadingRecommended,
    recommendedUnavailable,
    fetchRelated,
  } = usePaperDetail(paper)

  useEffect(() => {
    if (paper?.id) {
      fetchRelated()
    }
  }, [paper?.id, fetchRelated])

  if (loading) {
    return <EmptyState message="Loading paper…" />
  }

  if (error) {
    return <EmptyState message={error} />
  }

  if (!paper) {
    return <EmptyState message="Paper not found." />
  }

  return (
    <div className="paper-view-exploration">
      <div className="paper-view-current">
        {meta && <p className="paper-view-meta">{meta}</p>}
        <h2 className="paper-view-title">{paper.title}</h2>
        <p className="paper-view-abstract">{paper.abstract}</p>

        <div className="paper-view-actions">
          {paper.url ? (
            <a
              className="paper-view-link-btn"
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              View full paper ↗
            </a>
          ) : (
            <button className="paper-view-link-btn" disabled style={{ opacity: 0.3, cursor: "default" }}>
              No source link
            </button>
          )}
        </div>
      </div>

      <div className="paper-view-columns">
        <section className="paper-view-column">
          {loadingRelated && <EmptyState message="Finding related papers…" />}

          {!loadingRelated && related && related.length === 0 && (
            <EmptyState message="No related papers found." />
          )}

          {!loadingRelated && related && related.length > 0 && (
            <ResultsList
              docs={related}
              onSelect={onPaperSelect}
              label="Related papers"
              compact
            />
          )}
        </section>

        <section className="paper-view-column">
          <RecommendationPanel
            recommendations={recommended}
            loading={loadingRecommended}
            unavailable={recommendedUnavailable}
            onTitleClick={onPaperSelect}
          />
        </section>
      </div>
    </div>
  )
}
