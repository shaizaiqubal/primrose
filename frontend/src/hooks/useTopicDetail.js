import { useEffect, useState } from "react"
import { getTopic, getTopicPapers } from "../api.js"
import { normalizeTopic } from "../utils/topics.js"

export default function useTopicDetail(topicId) {
  const [topic, setTopic] = useState(null)
  const [loadingTopic, setLoadingTopic] = useState(false)
  const [topicError, setTopicError] = useState("")
  const [papers, setPapers] = useState(null)
  const [loadingPapers, setLoadingPapers] = useState(false)
  const [papersError, setPapersError] = useState("")

  useEffect(() => {
    if (!topicId) return

    let cancelled = false

    const loadTopic = async () => {
      setLoadingTopic(true)
      setTopic(null)
      setTopicError("")
      setLoadingPapers(true)
      setPapers(null)
      setPapersError("")

      try {
        const detail = await getTopic(topicId)
        if (!cancelled) setTopic(normalizeTopic(detail))
      } catch (err) {
        console.error("Topic detail load failed:", err)
        if (!cancelled) {
          if (err?.response?.status === 404) {
            setTopicError("Topic not found.")
          } else {
            setTopicError("Unable to load topic.")
          }
          setLoadingPapers(false)
        }
        return
      } finally {
        if (!cancelled) setLoadingTopic(false)
      }

      try {
        const topicPapers = await getTopicPapers(topicId)
        if (!cancelled) setPapers(topicPapers)
      } catch (err) {
        console.error("Topic papers load failed:", err)
        if (!cancelled) {
          setPapers([])
          setPapersError("Unable to load papers for this topic.")
        }
      } finally {
        if (!cancelled) setLoadingPapers(false)
      }
    }

    loadTopic()

    return () => {
      cancelled = true
    }
  }, [topicId])

  return { topic, loadingTopic, topicError, papers, loadingPapers, papersError }
}
