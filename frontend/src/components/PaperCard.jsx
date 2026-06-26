import { useState } from "react"

const css = `
  .paper-card {
    padding: 28px 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }

  .paper-card + .paper-card {
    border-top: none;
  }

  .paper-card-meta {
    font-size: 11px;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
  }

  .paper-card-title {
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 1.2rem;
    font-weight: normal;
    line-height: 1.35;
    color: var(--text);
    margin-bottom: 14px;
  }


  .paper-card-abstract {
    font-size: 14px;
    line-height: 1.75;
    color: var(--text);
    opacity: 0.82;
    margin-bottom: 6px;
  }

  .paper-card-abstract.clamped {
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: hidden;
    -webkit-mask-image: linear-gradient(to bottom, black 0%, black 70%, transparent 100%);
    mask-image: linear-gradient(to bottom, black 0%, black 70%, transparent 100%);
  }

  .read-more-btn {
    background: none;
    border: none;
    padding: 0;
    font-family: 'Work Sans', sans-serif;
    font-size: 13px;
    color: var(--muted);
    cursor: pointer;
    margin-bottom: 20px;
    transition: color 0.15s;
    display: inline-block;
  }

  .read-more-btn:hover {
    color: var(--accent);
  }

  .paper-card-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
  }

  .card-action-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: 'Work Sans', sans-serif;
    font-size: 12px;
    letter-spacing: 0.04em;
    padding: 6px 14px;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .card-action-btn:hover {
    color: var(--accent);
    border-color: var(--accent);
  }
`

function formatMeta(doc) {
  const parts = []
  if (doc.authors) parts.push(doc.authors)
  if (doc.year_published) parts.push(doc.year_published)
  return parts.join(" · ")
}

export default function PaperCard({ doc, onRelated, showRelatedAction = true }) {
  const [expanded, setExpanded] = useState(false)

  const meta = formatMeta(doc)

  return (
    <>
      <style>{css}</style>
      <div className="paper-card">
        {meta && <p className="paper-card-meta">{meta}</p>}
        <h2 className="paper-card-title">{doc.title}</h2>

        <p className={`paper-card-abstract ${expanded ? "" : "clamped"}`}>
          {doc.abstract}
        </p>

        <button
          className="read-more-btn"
          onClick={() => setExpanded((e) => !e)}
        >
          {expanded ? "↑ collapse" : "read more ↓"}
        </button>

        <div className="paper-card-actions">
          {doc.url ? (
            <a
              className="card-action-btn"
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              View full paper ↗
            </a>
          ) : (
            <button className="card-action-btn" disabled style={{ opacity: 0.3, cursor: "default" }}>
              No source link
            </button>
          )}
          {showRelatedAction && (
            <button className="card-action-btn" onClick={() => onRelated(doc)}>
              Related
            </button>
          )}
        </div>
      </div>
    </>
  )
}
