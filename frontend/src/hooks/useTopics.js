import { useEffect, useState } from "react"
import { getTopics } from "../api.js"

export default function useTopics() {
  const [topics, setTopics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const loadTopics = async () => {
      setLoading(true)
      setError("")
      try {
        const data = await getTopics()
        if (!cancelled) setTopics(data)
      } catch (err) {
        console.error("Topics load failed:", err)
        if (!cancelled) {
          setTopics([])
          setError("Unable to load topics.")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadTopics()

    return () => {
      cancelled = true
    }
  }, [])

  return { topics, loading, error }
}
