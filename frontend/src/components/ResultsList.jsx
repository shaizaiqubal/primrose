import PaperCard from "./PaperCard.jsx"

const css = `
  .results-label {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 20px;
  }

`

export default function ResultsList({ docs, onRelated, label, compact = false, onSelect }) {
  if (!docs || docs.length === 0) return null

  const heading = label ?? `${docs.length} result${docs.length !== 1 ? "s" : ""}`

  return (
      <>
      <style>{css}</style>
      <p className="results-label">{heading}</p>
      {docs.map((doc) => (
        <PaperCard
          key={doc.id}
          doc={doc}
          onTitleClick={compact ? onSelect : onRelated}
          compact={compact}
        />
      ))}
    </>
  )
}
