import { useCallback, useEffect, useState } from "react"
import { getRelated, getRecommended } from "../api.js"

export default function usePaperDetail(paper) {
  const [related, setRelated] = useState(null)
  const [loadingRelated, setLoadingRelated] = useState(false)
  const [recommended, setRecommended] = useState(null)
  const [loadingRecommended, setLoadingRecommended] = useState(false)
  const [recommendedUnavailable, setRecommendedUnavailable] = useState(false)
  const paperId = paper?.id ?? null

  const fetchRelated = useCallback(async () => {
    if (!paperId) return

    setLoadingRelated(true)
    setRelated(null)
    try {
      const results = await getRelated(paperId)
      setRelated(results)
    } catch (err) {
      console.error("Related fetch failed:", err)
      setRelated([])
    } finally {
      setLoadingRelated(false)
    }
  }, [paperId])

  useEffect(() => {
    let cancelled = false

    const loadRecommended = async () => {
      if (!paperId) return

      setLoadingRecommended(true)
      setRecommended(null)
      setRecommendedUnavailable(false)
      try {
        const docs = await getRecommended(paperId)
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
  }, [paperId])

  return {
    related,
    loadingRelated,
    recommended,
    loadingRecommended,
    recommendedUnavailable,
    fetchRelated,
  }
}
