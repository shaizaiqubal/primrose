const css = `
  .topbar {
    position: static;
    top: 0;
    z-index: 10;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    padding: 24px 48px;
    height: 80px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    column-gap: 24px;
  }

  .wordmark {
    font-family: 'Anvers', 'Work Sans', serif;
    font-size: 1rem;
    font-weight: 400;
    letter-spacing: 0.04em;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
    justify-self: center;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    justify-self: start;
  }
 
  .wordmark-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    display: inline-block;
    flex-shrink: 0;
  }

  .topbar-nav {
    display: flex;
    gap: 20px;
    align-items: center;
  }

  .topbar-right {
    display: flex;
    align-items: center;
    justify-self: end;
  }

  .nav-btn {
    background: none;
    border: 1px solid var(--border);
    border-radius: 50%;
    color: var(--muted);
    width: 32px;
    height: 32px;
    font-family: 'Work Sans', sans-serif;
    font-size: 13px;
    cursor: pointer;
    padding: 4px 0;
    transition: color 0.15s;
    letter-spacing: 0.02em;
  }

  .nav-btn:hover:not(:disabled) {
    color: var(--accent);
    border-color: var(--accent);
  }

  .nav-btn:disabled {
    opacity: 0.3;
    cursor: default;
  }

  .theme-toggle {
    background: none;
    border: 1px solid var(--border);
    border-radius: 50%;
    color: var(--muted);
    font-family: 'Work Sans', sans-serif;
    font-size: 22px;
    width: 32px;
    height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .theme-toggle:hover {
    color: var(--accent);
    border-color: var(--accent);
  }
`

export default function TopBar({ onHome, onBack, onForward, canBack, canForward, theme, onToggleTheme }) {
  return (
    <>
      <style>{css}</style>
      <header className="topbar">
        <nav className="topbar-nav topbar-left">
          <button className="nav-btn" onClick={onBack} disabled={!canBack}>
          ← 
          </button>
          <button className="nav-btn" onClick={onForward} disabled={!canForward}>
            →
          </button>
        </nav>
        <button className="wordmark" onClick={onHome}>
          <span className="wordmark-dot" />
          Primrose
        </button>
        <div className="topbar-right">
          <button
            className="theme-toggle"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? "☼" : "☾"}
          </button>
        </div>
      </header>
    </>
  )
}
