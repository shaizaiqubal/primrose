import { useEffect, useState } from "react"
import { getDocuments } from "../api.js"

export default function useBrowseDocs() {
  const [docs, setDocs] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false

    const loadBrowseDocs = async () => {
      setLoading(true)
      try {
        const data = await getDocuments()
        if (!cancelled) setDocs(data)
      } catch (err) {
        console.error("Browse load failed:", err)
        if (!cancelled) setDocs([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadBrowseDocs()

    return () => {
      cancelled = true
    }
  }, [])

  return { docs, loading }
}
