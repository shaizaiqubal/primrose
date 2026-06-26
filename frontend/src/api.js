import axios from "axios"

const api = axios.create({
  baseURL: "http://localhost:8000"
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