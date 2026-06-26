const css = `
  .search-label {
    display: block;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .search-row {
    display: flex;
    gap: 8px;
  }

  .search-input {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'Work Sans', sans-serif;
    font-size: 14px;
    padding: 10px 14px;
    outline: none;
    transition: border-color 0.15s;
  }

  .search-input::placeholder {
    color: var(--muted);
  }

  .search-input:focus {
    border-color: var(--muted);
  }

  .search-btn {
    background: var(--accent);
    border: none;
    color: var(--bg);
    font-family: 'Work Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 10px 20px;
    cursor: pointer;
    transition: opacity 0.15s;
    border-radius: 0;
    appearance: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    white-space: nowrap;
  }

  .search-btn:hover:not(:disabled) {
    opacity: 0.88;
  }

  .search-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
`

export default function SearchBar({ query, setQuery, onSearch, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim())
  }

  return (
    <>
      <style>{css}</style>
      <form onSubmit={handleSubmit}>
        <label className="search-label" htmlFor="primrose-search">
          Search
        </label>
        <div className="search-row">
          <input
            id="primrose-search"
            className="search-input"
            type="text"
            placeholder="Describe what you're looking for..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <button className="search-btn" type="submit" disabled={loading || !query.trim()}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
      </form>
    </>
  )
}
