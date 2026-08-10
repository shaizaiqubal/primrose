import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL
})

export const getDocuments = async () => {
  const response = await api.get("/documents")
  return response.data
}

export const getTopics = async () => {
  const response = await api.get("/topics")
  return response.data
}

export const getTopic = async (topicId) => {
  const response = await api.get(`/topics/${topicId}`)
  return response.data
}

export const getTopicPapers = async (topicId) => {
  const response = await api.get(`/topics/${topicId}/papers`)
  return response.data
}

export const getDocument = async (id) => {
  const response = await api.get(`/documents/${id}`)
  return response.data
}

export const getRelated = async (id) => {
  const response = await api.get(`/documents/${id}/related`)
  return response.data.map(r => ({ ...r.document, relevance_score: r.relevance_score }))
}

export const searchDocuments = async (query) => {
  const response = await api.get(
    `/documents/search`,
    {
      params: { query }
    }
  )
  console.log("raw related response:", response.data)

  return response.data.map(r => ({ ...r.document, relevance_score: r.relevance_score }))
}

export const getRecommended = async (id) => {
  const response = await api.get(`/documents/${id}/recommendations`)
  return response.data
}
