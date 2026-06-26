const css = `
  .empty-state {
    font-size: 14px;
    color: var(--muted);
    padding: 40px 0;
  }
`

export default function EmptyState({ message }) {
  return (
    <>
      <style>{css}</style>
      <p className="empty-state">{message}</p>
    </>
  )
}