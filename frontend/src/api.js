import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL
})

export const getDocuments = async () => {
  const response = await api.get("/documents")
  return response.data
}

export const getDocument = async (id) => {
  const response = await api.get(`/documents/${id}`)
  return response.data
}

export const getRelated = async (id) => {
  const response = await api.get(`/documents/${id}/related`)
  return response.data
}

export const searchDocuments = async (query) => {
  const response = await api.get(
    `/documents/search`,
    {
      params: { query }
    }
  )

  return response.data
}