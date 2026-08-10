import SearchBar from "../components/SearchBar.jsx"
import ResultsList from "../components/ResultsList.jsx"
import EmptyState from "../components/EmptyState.jsx"

export default function HomeView({
  searchQuery,
  setSearchQuery,
  onSearch,
  loadingSearch,
  searchResults,
  onPaperSelect,
  browseDocs,
  loadingBrowse,
  onTopics,
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

      <div className="home-topic-cta-wrap">
        <button type="button" className="home-topic-eyebrow" onClick={onTopics}>
          or browse research topics →
        </button>
      </div>

      {!loadingSearch && searchResults !== null && searchResults.length === 0 && (
        <EmptyState message="No results found." />
      )}

      {!loadingSearch && searchResults && searchResults.length > 0 && (
        <ResultsList
          docs={searchResults}
          onSelect={onPaperSelect}
        />
      )}

      {!searchResults && loadingBrowse && <EmptyState message="Loading papers…" />}

      {!searchResults && !loadingBrowse && browseDocs && browseDocs.length > 0 && (
        <ResultsList
          docs={browseDocs}
          label="Browse Papers"
          compact
          onSelect={onPaperSelect}
        />
      )}

      {!searchResults && !loadingBrowse && browseDocs && browseDocs.length === 0 && (
        <EmptyState message="No papers available." />
      )}
    </>
  )
}
