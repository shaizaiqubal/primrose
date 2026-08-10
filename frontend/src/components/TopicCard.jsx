const css = `
  .topic-card {
    width: 100%;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    padding: 18px 0;
    background: none;
    border: none;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    cursor: pointer;
    text-align: left;
  }

  .topic-card:first-child {
    border-top: 1px solid var(--border);
  }

  .topic-card:hover .topic-card-title {
    color: var(--accent);
  }

  .topic-card-body {
    min-width: 0;
    flex: 1;
  }

  .topic-card-title {
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 0.95rem;
    line-height: 1.4;
    font-weight: normal;
    color: var(--text);
    margin: 0;
  }

  .topic-card-count {
    flex: 0 0 auto;
    font-size: 0.6875rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    padding-top: 0.15rem;
    white-space: nowrap;
  }
`

export default function TopicCard({ topic, onClick }) {
  return (
    <>
      <style>{css}</style>
      <button type="button" className="topic-card" onClick={() => onClick?.(topic)}>
        <div className="topic-card-body">
          <h3 className="topic-card-title">{topic.name}</h3>
        </div>
        <span className="topic-card-count">
          {topic.paper_count} paper{topic.paper_count === 1 ? "" : "s"}
        </span>
      </button>
    </>
  )
}
