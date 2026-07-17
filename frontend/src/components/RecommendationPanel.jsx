import { useState } from "react"
import EmptyState from "./EmptyState.jsx"
import ChevronToggleButton from "./ChevronToggleButton.jsx"
import { formatDocumentMeta } from "../utils/formatDocumentMeta.js"

function RecommendationItem({ doc, position, onTitleClick }) {
  const [expanded, setExpanded] = useState(false)
  const meta = formatDocumentMeta(doc)

  return (
    <article className="recommendation-item">
      <div className="recommendation-item-header">
        <span className="recommendation-item-position">{position}</span>
        <div className="recommendation-item-heading-block">
          {meta && <p className="recommendation-item-meta">{meta}</p>}
          <button
            type="button"
            className="recommendation-item-title"
            onClick={() => onTitleClick?.(doc)}
          >
            {doc.title}
          </button>
        </div>
      </div>

      {doc.recommendation_note && (
        <p className="recommendation-item-note">{doc.recommendation_note}</p>
      )}

      {doc.abstract && (
        <div className="recommendation-item-abstract-wrap">
          {expanded && <p className="recommendation-item-abstract">{doc.abstract}</p>}
          <ChevronToggleButton
            expanded={expanded}
            onClick={() => setExpanded((e) => !e)}
            ariaLabel={expanded ? "Collapse abstract" : "Expand abstract"}
            className="recommendation-item-chevron"
          />
        </div>
      )}
    </article>
  )
}

const css = `
  .recommendation-panel {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 18px;
    border: none;
    border-radius: 0;
  }

  .recommendation-panel-title {
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 1.1rem;
    font-weight: normal;
    line-height: 1.3;
    color: var(--text);
  }

  .recommendation-panel-body {
    flex: 1;
    min-height: 0;
  }

  .recommendation-panel-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .recommendation-item {
    padding: 14px 14px 14px;
    background: transparent;
  }

  .recommendation-item:not(:last-child)::after {
    content: "";
    display: block;
    border-bottom: 1px solid var(--accent);
    margin-top: 14px;
  }

  .recommendation-item-meta {
    font-size: 0.6875rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.375rem;
  }

  .recommendation-item-title {
    display: block;
    width: 100%;
    background: none;
    border: none;
    padding: 0;
    text-align: left;
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 0.9375rem;
    line-height: 1.35;
    font-weight: normal;
    color: var(--text);
    margin-bottom: 0;
    cursor: pointer;
  }

  .recommendation-item-title:hover {
    color: var(--accent);
  }

  .recommendation-item-header {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 0.5rem;
  }

  .recommendation-item-position {
    flex: 0 0 auto;
    min-width: 1.5rem;
    height: 1.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--accent);
    border-radius: 999px;
    color: var(--accent);
    font-size: 0.75rem;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    margin-top: 0.1rem;
  }

  .recommendation-item-heading-block {
    min-width: 0;
    flex: 1;
  }

  .recommendation-item-note {
    font-size: 0.8125rem;
    line-height: 1.65;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .recommendation-item-abstract {
    font-size: 0.8125rem;
    line-height: 1.7;
    color: var(--text);
    opacity: 0.85;
    margin-bottom: 0;
  }

  .recommendation-item-abstract-wrap {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .recommendation-item-chevron {
    align-self: flex-start;
  }

  .recommendation-item-chevron .chevron-toggle-icon {
    width: 1.05rem;
    height: 1.05rem;
  }
`

export default function RecommendationPanel({ recommendations, loading, unavailable, onTitleClick }) {
  const orderedRecommendations = (recommendations ?? [])
    .slice()
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
    .slice(0, 5)

  return (
    <div className="recommendation-panel">
      <style>{css}</style>
      <h2 className="recommendation-panel-title">Reading Journey</h2>

      <div className="recommendation-panel-body">
        {unavailable && <EmptyState message="Recommendations are unavailable." />}

        {loading && <EmptyState message="Recommendations will appear here." />}

        {!loading && !unavailable && (!recommendations || recommendations.length === 0) && (
          <EmptyState message="Recommendations will appear here." />
        )}

        {!loading && !unavailable && orderedRecommendations.length > 0 && (
          <div className="recommendation-panel-list">
            {orderedRecommendations.map((doc, index) => (
              <RecommendationItem
                key={doc.id}
                doc={doc}
                position={doc.position ?? index + 1}
                onTitleClick={onTitleClick}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
