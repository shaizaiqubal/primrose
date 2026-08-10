import { useEffect, useState } from "react"
import { getDocument } from "../api.js"

export default function usePaperById(paperId) {
  const [paper, setPaper] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!paperId) return

    let cancelled = false

    const loadPaper = async () => {
      setLoading(true)
      setPaper(null)
      setError("")
      try {
        const data = await getDocument(paperId)
        if (!cancelled) setPaper(data)
      } catch (err) {
        console.error("Paper detail load failed:", err)
        if (!cancelled) {
          if (err?.response?.status === 404) {
            setError("Paper not found.")
          } else {
            setError("Unable to load paper.")
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadPaper()

    return () => {
      cancelled = true
    }
  }, [paperId])

  return { paper, loading, error }
}
