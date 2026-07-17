import { useState } from "react"
import ChevronToggleButton from "./ChevronToggleButton.jsx"
import { formatDocumentMeta } from "../utils/formatDocumentMeta.js"

const css = `
  .paper-card {
    padding-block: 1rem;
    border-bottom: 1px solid var(--border);
  }

  .paper-card.compact {
    padding-block: 1rem;
  }

  .paper-card:first-child {
    border-top: 1px solid var(--border);
  }

  .paper-card-meta {
    font-size: 0.6875rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.375rem;
  }

  .paper-card-title {
    flex: 1 1 auto;
    min-width: 0;
    display: block;
    background: none;
    border: none;
    padding: 0;
    text-align: left;
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 0.9375rem;
    font-weight: normal;
    line-height: 1.35;
    color: var(--text);
    margin-bottom: 0;
    cursor: pointer;
  }

  .paper-card-title:hover {
    color: var(--accent);
  }

  .paper-card-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 0.375rem;
  }

  .paper-card.compact .paper-card-header {
    margin-bottom: 0.25rem;
  }

  .paper-card.compact .paper-card-meta {
    margin-bottom: 0.25rem;
  }

  .paper-card.compact .paper-card-abstract {
    margin-bottom: 0.875rem;
  }

  .chevron-toggle-btn {
    background: none;
    border: none;
    padding: 0;
    color: var(--muted);
    cursor: pointer;
    flex-shrink: 0;
    display: inline-flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 0.1rem;
  }

  .chevron-toggle-btn:hover {
    color: var(--accent);
  }

  .chevron-toggle-icon {
    width: 1rem;
    height: 1rem;
    stroke-width: 2.2;
    transition: transform 0.16s ease, color 0.15s ease;
  }

  .chevron-toggle-icon.expanded {
    transform: rotate(180deg);
  }

  .paper-card-abstract {
    font-size: 0.8125rem;
    line-height: 1.75;
    color: var(--text);
    opacity: 0.82;
    margin-bottom: 20px;
  }
`

export default function PaperCard({ doc, onTitleClick, compact = false }) {
  const [expanded, setExpanded] = useState(false)

  const meta = formatDocumentMeta(doc)

  return (
    <>
      <style>{css}</style>
      <div className={`paper-card ${compact ? "compact" : ""}`}>
        {meta && <p className="paper-card-meta">{meta}</p>}
        <div className="paper-card-header">
          <button type="button" className="paper-card-title" onClick={() => onTitleClick?.(doc)}>
            {doc.title}
          </button>
          <ChevronToggleButton
            expanded={expanded}
            onClick={() => setExpanded((e) => !e)}
            ariaLabel={expanded ? "Collapse abstract" : "Expand abstract"}
          />
        </div>

        {expanded && (
          <p className="paper-card-abstract">
            {doc.abstract}
          </p>
        )}
      </div>
    </>
  )
}
