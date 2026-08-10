import { useCallback, useState } from "react"
import { searchDocuments } from "../api.js"

export default function useSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (input) => {
    setLoading(true)
    setResults(null)
    try {
      const docs = await searchDocuments(input)
      setResults(docs)
    } catch (err) {
      console.error("Search failed:", err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const clearSearch = useCallback(() => {
    setResults(null)
    setQuery("")
  }, [])

  return { query, setQuery, results, loading, search, clearSearch }
}
