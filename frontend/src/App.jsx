import { useEffect, useState, useCallback } from "react"
import { Route, Routes, useLocation, useNavigate } from "react-router-dom"

import TopBar from "./components/TopBar.jsx"
import HomeView from "./views/HomeView.jsx"
import PaperView from "./views/PaperView.jsx"
import TopicDetailView from "./views/TopicDetailView.jsx"
import TopicListView from "./views/TopicListView.jsx"
import useBrowseDocs from "./hooks/useBrowseDocs.js"
import useSearch from "./hooks/useSearch.js"
import { topicId } from "./utils/topics.js"

import "./App.css"

const MAX_HISTORY_INDEX_KEY = "primrose-max-history-index"

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const isTopicsRoute = location.pathname.startsWith("/topics")
  const isPaperRoute = location.pathname.startsWith("/papers")
  const [theme, setTheme] = useState(() => {
    const saved = window.localStorage.getItem("primrose-theme")
    if (saved === "dark" || saved === "light") return saved
    return "dark"
  })

  const {
    query: searchQuery,
    setQuery: setSearchQuery,
    results: searchResults,
    loading: loadingSearch,
    search: handleSearch,
    clearSearch,
  } = useSearch()
  const { docs: browseDocs, loading: loadingBrowse } = useBrowseDocs()

  useEffect(() => {
    document.body.classList.remove("theme-dark", "theme-light")
    document.body.classList.add(`theme-${theme}`)
    window.localStorage.setItem("primrose-theme", theme)
  }, [theme])

  useEffect(() => {
    const currentIndex = window.history.state?.idx ?? 0
    const previousMax = Number(window.sessionStorage.getItem(MAX_HISTORY_INDEX_KEY) ?? "0")
    if (currentIndex > previousMax) {
      window.sessionStorage.setItem(MAX_HISTORY_INDEX_KEY, String(currentIndex))
    }
  }, [location.key])

  const handleNavigateHome = useCallback(() => {
    navigate("/")
    clearSearch()
    window.scrollTo(0, 0)
  }, [clearSearch, navigate])

  const handleNavigateTopics = useCallback(() => {
    navigate("/topics")
    window.scrollTo(0, 0)
  }, [navigate])

  const handleOpenTopic = useCallback((topic) => {
    const id = topicId(topic)
    if (!id) return
    navigate(`/topics/${id}`)
    window.scrollTo(0, 0)
  }, [navigate])

  const handleSelectPaper = useCallback((doc) => {
    if (!doc?.id) return
    navigate(`/papers/${doc.id}`)
    window.scrollTo(0, 0)
  }, [navigate])

  const handleBack = useCallback(() => {
    if (location.pathname === "/" && searchResults !== null) {
      clearSearch()
      window.scrollTo(0, 0)
      return
    }
    navigate(-1)
    window.scrollTo(0, 0)
  }, [clearSearch, location.pathname, navigate, searchResults])

  const handleForward = useCallback(() => {
    navigate(1)
    window.scrollTo(0, 0)
  }, [navigate])

  const historyIndex = window.history.state?.idx ?? 0
  const canBack = (location.pathname === "/" && searchResults !== null) || historyIndex > 0
  const maxHistoryIndex = Number(window.sessionStorage.getItem(MAX_HISTORY_INDEX_KEY) ?? String(historyIndex))
  const canForward = historyIndex < maxHistoryIndex

  return (
    <>
      <TopBar
        onHome={handleNavigateHome}
        onTopics={handleNavigateTopics}
        onBack={handleBack}
        onForward={handleForward}
        canBack={canBack}
        canForward={canForward}
        theme={theme}
        onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        topicsActive={isTopicsRoute}
      />

      <main className={`main ${isPaperRoute ? "paper-view-main" : ""} ${isTopicsRoute ? "topics-view-main" : ""}`}>
        <Routes>
          <Route
            path="/"
            element={(
              <HomeView
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                onSearch={handleSearch}
                loadingSearch={loadingSearch}
                searchResults={searchResults}
                onPaperSelect={handleSelectPaper}
                browseDocs={browseDocs}
                loadingBrowse={loadingBrowse}
                onTopics={handleNavigateTopics}
              />
            )}
          />
          <Route
            path="/topics"
            element={(
              <TopicListView
                onTopicClick={handleOpenTopic}
              />
            )}
          />
          <Route
            path="/topics/:topicId"
            element={(
              <TopicDetailView
                onPaperSelect={handleSelectPaper}
              />
            )}
          />
          <Route
            path="/papers/:paperId"
            element={(
              <PaperView
                onPaperSelect={handleSelectPaper}
              />
            )}
          />
        </Routes>
      </main>
    </>
  )
}
