import { useEffect, useState, useCallback } from "react"
import { getDocuments, getRelated, getRecommended, searchDocuments } from "./api.js"

import TopBar from "./components/TopBar.jsx"
import SearchBar from "./components/SearchBar.jsx"
import ResultsList from "./components/ResultsList.jsx"
import EmptyState from "./components/EmptyState.jsx"
import RecommendationPanel from "./components/RecommendationPanel.jsx"
import { formatDocumentMeta } from "./utils/formatDocumentMeta.js"

import "./App.css"
// ─── Views ───────────────────────────────────────────────────────────────────

function HomeView({
  searchQuery,
  setSearchQuery,
  onSearch,
  loadingSearch,
  searchResults,
  onRelated,
  browseDocs,
  loadingBrowse,
  onBrowseSelect,
}) {
  return (
    <>
      <h1 className="home-heading">Explore research beyond keywords.</h1>
      <p className="home-sub">Primrose goes beyond keyword matching to surface relevant literature, papers, and sources using semantic understanding.</p>

      <div className="search-wrap">
        <SearchBar
          query={searchQuery}
          setQuery={setSearchQuery}
          onSearch={onSearch}
          loading={loadingSearch}
        />
      </div>

      {!loadingSearch && searchResults !== null && searchResults.length === 0 && (
        <EmptyState message="No results found." />
      )}

      {!loadingSearch && searchResults && searchResults.length > 0 && (
        <ResultsList
          docs={searchResults}
          onRelated={onRelated}
        />
      )}

      {!searchResults && loadingBrowse && <EmptyState message="Loading papers…" />}

      {!searchResults && !loadingBrowse && browseDocs && browseDocs.length > 0 && (
        <ResultsList
          docs={browseDocs}
          label="Browse Papers"
          compact
          onSelect={onBrowseSelect}
        />
      )}

      {!searchResults && !loadingBrowse && browseDocs && browseDocs.length === 0 && (
        <EmptyState message="No papers available." />
      )}
    </>
  )
}

function PaperView({
  paper,
  onRelated,
  onRecommendedTitleClick,
  related,
  loadingRelated,
  recommended,
  loadingRecommended,
  unavailable,
}) {
  const meta = formatDocumentMeta(paper)

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
              onRelated={onRelated}
              label="Related papers"
              compact
              onSelect={onRelated}
            />
          )}
        </section>

        <section className="paper-view-column">
          <RecommendationPanel
            recommendations={recommended}
            loading={loadingRecommended}
            unavailable={unavailable}
            onTitleClick={onRecommendedTitleClick}
          />
        </section>
      </div>
    </div>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [view, setView] = useState("home")         // "home" | "paper"
  const [currentPaper, setCurrentPaper] = useState(null)
  const [history, setHistory] = useState([])        // stack of { paper, related }
  const [future, setFuture] = useState([])          // for forward navigation
  const [theme, setTheme] = useState(() => {
    const saved = window.localStorage.getItem("primrose-theme")
    if (saved === "dark" || saved === "light") return saved
    return "dark"
  })

  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState(null)
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [browseDocs, setBrowseDocs] = useState(null)
  const [loadingBrowse, setLoadingBrowse] = useState(false)

  const [related, setRelated] = useState(null)
  const [loadingRelated, setLoadingRelated] = useState(false)
  const [recommended, setRecommended] = useState(null)
  const [loadingRecommended, setLoadingRecommended] = useState(false)
  const [recommendedUnavailable, setRecommendedUnavailable] = useState(false)

  useEffect(() => {
    document.body.classList.remove("theme-dark", "theme-light")
    document.body.classList.add(`theme-${theme}`)
    window.localStorage.setItem("primrose-theme", theme)
  }, [theme])

  const currentPaperId = currentPaper?.id

  useEffect(() => {
    if (view !== "paper" || !currentPaperId) return

    let cancelled = false

    const loadRecommended = async () => {
      setLoadingRecommended(true)
      setRecommended(null)
      setRecommendedUnavailable(false)
      try {
        const docs = await getRecommended(currentPaperId)
        if (!cancelled) setRecommended(docs)
      } catch (err) {
        console.error("Recommendation fetch failed:", err)
        if (!cancelled) {
          if (err?.response?.status === 503) {
            setRecommendedUnavailable(true)
          } else {
            setRecommended([])
          }
        }
      } finally {
        if (!cancelled) setLoadingRecommended(false)
      }
    }

    loadRecommended()

    return () => {
      cancelled = true
    }
  }, [view, currentPaperId])

  useEffect(() => {
    let cancelled = false

    const loadBrowseDocs = async () => {
      setLoadingBrowse(true)
      try {
        const docs = await getDocuments()
        if (!cancelled) setBrowseDocs(docs)
      } catch (err) {
        console.error("Browse load failed:", err)
        if (!cancelled) setBrowseDocs([])
      } finally {
        if (!cancelled) setLoadingBrowse(false)
      }
    }

    loadBrowseDocs()

    return () => {
      cancelled = true
    }
  }, [])

  // ── Search ──
  const handleSearch = useCallback(async (query) => {
    setLoadingSearch(true)
    setSearchResults(null)
    try {
      const results = await searchDocuments(query)
      setSearchResults(results)
    } catch (err) {
      console.error("Search failed:", err)
      setSearchResults([])
    } finally {
      setLoadingSearch(false)
    }
  }, [])

  const clearSearch = useCallback(() => {
    setSearchResults(null)
    setSearchQuery("")
  }, [])

  // ── Select a paper (from results or related list) ──
  const handleSelectPaper = useCallback((doc) => {
    if (currentPaper) {
      setHistory((h) => [...h, { paper: currentPaper, related }])
    }
    setFuture([])
    setCurrentPaper(doc)
    setRelated(null)
    setRecommended(null)
    setLoadingRecommended(false)
    setRecommendedUnavailable(false)
    setView("paper")
    window.scrollTo(0, 0)
  }, [currentPaper, related])

  // ── Fetch related ──
  const handleRelated = useCallback(async (doc) => {
  // navigate to the paper first
    if (currentPaper?.id !== doc.id) {
      handleSelectPaper(doc)
    }
    // then fetch related
    setLoadingRelated(true)
    setRelated(null)
    try {
      const results = await getRelated(doc.id)
      setRelated(results)
    } catch (err) {
      console.error("Related fetch failed:", err)
      setRelated([])
    } finally {
      setLoadingRelated(false)
    }
  }, [currentPaper, handleSelectPaper])

  // ── Back ──
  const handleBack = useCallback(() => {
    if (history.length > 0) {
      const prev = history[history.length - 1]
      setFuture((f) => [{ paper: currentPaper, related }, ...f])
      setHistory((h) => h.slice(0, -1))
      setCurrentPaper(prev.paper)
      setRelated(prev.related)
      setRecommended(null)
      setLoadingRecommended(false)
      setRecommendedUnavailable(false)
      setView("paper")
    } else if (view === "paper") {
      setView("home")
      setCurrentPaper(null)
      setRelated(null)
      setRecommended(null)
      setLoadingRecommended(false)
      setRecommendedUnavailable(false)
    } else if (searchResults !== null) {
      clearSearch()
    }
    window.scrollTo(0, 0)
  }, [history, currentPaper, related, view, searchResults, clearSearch])

  // ── Forward ──
  const handleForward = () => {
    if (future.length === 0) return
    const next = future[0]
    setHistory((h) => [...h, { paper: currentPaper, related }])
    setFuture((f) => f.slice(1))
    setCurrentPaper(next.paper)
    setRelated(next.related)
    setRecommended(null)
    setLoadingRecommended(false)
    setRecommendedUnavailable(false)
    setView("paper")
    window.scrollTo(0, 0)
  }

  // ── Go home ──
  const handleHome = useCallback(() => {
    setView("home")
    setCurrentPaper(null)
    setRelated(null)
    setHistory([])
    setFuture([])
    clearSearch()
    window.scrollTo(0, 0)
  }, [clearSearch])

  const canBack = history.length > 0 || view === "paper" || searchResults !== null
  const canForward = future.length > 0

  return (
    <>
      <TopBar
        onHome={handleHome}
        onBack={handleBack}
        onForward={handleForward}
        canBack={canBack}
        canForward={canForward}
        theme={theme}
        onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      />

      <main className={`main ${view === "paper" ? "paper-view-main" : ""}`}>
        {view === "home" && (
          <HomeView
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onSearch={handleSearch}
            loadingSearch={loadingSearch}
            searchResults={searchResults}
            onRelated={handleRelated}
            browseDocs={browseDocs}
            loadingBrowse={loadingBrowse}
            onBrowseSelect={handleRelated}
          />
        )}

        {view === "paper" && currentPaper && (
          <PaperView
            paper={currentPaper}
            onRelated={handleRelated}
            onRecommendedTitleClick={handleRelated}
            related={related}
            loadingRelated={loadingRelated}
            recommended={recommended}
            loadingRecommended={loadingRecommended}
            unavailable={recommendedUnavailable}
          />
        )}
      </main>
    </>
  )
}
