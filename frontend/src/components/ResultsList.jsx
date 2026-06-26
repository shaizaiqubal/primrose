import PaperCard from "./PaperCard.jsx"

const css = `
  .results-label {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 20px;
  }

  .compact-paper-list {
    list-style: none;
  }

  .compact-paper-item {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    border-bottom: 1px solid var(--border);
    padding: 18px 0;
    cursor: pointer;
  }

  .compact-paper-item:first-child {
    border-top: 1px solid var(--border);
  }

  .compact-paper-item:hover .compact-paper-title {
    color: var(--accent);
  }

  .compact-paper-title {
    font-size: 15px;
    font-family: "Anvers", serif;
    font-weight: normal;
    line-height: 1.4;
    color: var(--text);
    margin-bottom: 6px;
    transition: color 0.15s;
  }

  .compact-paper-meta {
    font-size: 8px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
  }
`

function formatMeta(doc) {
  const parts = []
  if (doc.authors) parts.push(doc.authors)
  if (doc.year_published) parts.push(doc.year_published)
  return parts.join(" · ")
}

export default function ResultsList({ docs, onRelated, label, compact = false, onSelect }) {
  if (!docs || docs.length === 0) return null

  const heading = label ?? `${docs.length} result${docs.length !== 1 ? "s" : ""}`

  return (
    <>
      <style>{css}</style>
      <p className="results-label">{heading}</p>
      {compact ? (
        <ul className="compact-paper-list">
          {docs.map((doc) => (
            <li key={doc.id}>
              <button className="compact-paper-item" onClick={() => onSelect(doc)}>
                <div className="compact-paper-title">{doc.title}</div>
                <div className="compact-paper-meta">{formatMeta(doc)}</div>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        docs.map((doc) => (
          <PaperCard key={doc.id} doc={doc} onRelated={onRelated} />
        ))
      )}
    </>
  )
}
