export function topicName(topic) {
  return (
    topic?.topic_name?.trim()
    || topic?.cluster_name?.trim()
    || "Untitled topic"
  )
}

export function topicId(topic) {
  return topic?.topic_id ?? topic?.cluster_id ?? null
}

export function normalizeTopic(topic) {
  if (!topic) return null

  return {
    ...topic,
    name: topicName(topic),
  }
}
