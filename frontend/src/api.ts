import axios from 'axios'
import type { operations } from './api-schema'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('primrose-access-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

type ResponseBody<Operation extends keyof operations, Status extends keyof operations[Operation]['responses']> =
  operations[Operation]['responses'][Status] extends { content: { 'application/json': infer Body } }
    ? Body
    : never

export type Document = ResponseBody<'get_documents_documents_get', 200>[number]
export type RankedDocument = ResponseBody<'search_documents_documents_search_get', 200>[number]
export type Entity = ResponseBody<'list_entities_entities_get', 200>['items'][number]
export type EntitySearchResult = ResponseBody<'entity_search_entities_search_get', 200>[number]
export type Topic = ResponseBody<'topics_topics_get', 200>[number]
export type RecommendedPaper = ResponseBody<'get_recommendations_documents__id__recommendations_get', 200>[number]

export async function searchDocuments(query: string, entityId?: number) {
  const response = await api.get<ResponseBody<'search_documents_documents_search_get', 200>>(
    '/documents/search',
    { params: { query, ...(entityId ? { entities: entityId } : {}) } },
  )
  return response.data
}

export async function getDocuments(page = 1, pageSize = 50) {
  const response = await api.get<ResponseBody<'get_documents_documents_get', 200>>('/documents', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export async function listEntities(type?: string, page = 1, pageSize = 100) {
  const response = await api.get<ResponseBody<'list_entities_entities_get', 200>>('/entities', {
    params: { page, page_size: pageSize, ...(type ? { type } : {}) },
  })
  return response.data
}

export async function searchEntities(query: string, limit = 50, signal?: AbortSignal) {
  const response = await api.get<ResponseBody<'entity_search_entities_search_get', 200>>('/entities/search', {
    params: { q: query, limit },
    signal,
  })
  return response.data
}

export async function getDocument(id: number) {
  const response = await api.get<ResponseBody<'get_document_documents__id__get', 200>>(`/documents/${id}`)
  return response.data
}

export async function getDocumentEntities(id: number) {
  const response = await api.get<ResponseBody<'get_document_entities_documents__document_id__entities_get', 200>>(
    `/documents/${id}/entities`,
  )
  return response.data
}

export async function getRelatedDocuments(id: number) {
  const response = await api.get<ResponseBody<'get_related_documents_documents__id__related_get', 200>>(
    `/documents/${id}/related`,
  )
  return response.data
}

export async function getRecommendedPapers(id: number, signal?: AbortSignal) {
  const response = await api.get<ResponseBody<'get_recommendations_documents__id__recommendations_get', 200>>(
    `/documents/${id}/recommendations`,
    { signal },
  )
  return response.data
}

export async function addBookmark(id: number) {
  await api.post(`/documents/${id}/bookmark`)
}

export async function removeBookmark(id: number) {
  await api.delete(`/documents/${id}/bookmark`)
}

export async function logout(refreshToken: string | null) {
  if (refreshToken) {
    await api.post('/auth/logout', { refresh_token: refreshToken })
  }
}

export async function createDocument(document: import('./api-schema').components['schemas']['Document']) {
  const response = await api.post<Document>('/documents', document)
  return response.data
}

export async function deleteDocument(id: number) {
  await api.delete(`/documents/${id}`)
}

export async function getMyBookmarks() {
  const response = await api.get<ResponseBody<'get_user_bookmarks_me_bookmarks_get', 200>>('/me/bookmarks')
  return response.data
}

export async function getMyUploads() {
  const response = await api.get<ResponseBody<'get_user_uploads_me_uploads_get', 200>>('/me/uploads')
  return response.data
}

export async function getTopics() {
  const response = await api.get<ResponseBody<'topics_topics_get', 200>>('/topics')
  return response.data
}

export async function getTopic(id: number) {
  const response = await api.get<ResponseBody<'topic_topics__topic_id__get', 200>>(`/topics/${id}`)
  return response.data
}

export async function getTopicPapers(id: number, query?: string, page = 1, pageSize = 20) {
  const response = await api.get<ResponseBody<'topic_papers_topics__topic_id__papers_get', 200>>(
    `/topics/${id}/papers`,
    { params: { ...(query ? { query } : {}), page, page_size: pageSize } },
  )
  return response.data
}

export async function getEntityPapers(id: number) {
  const response = await api.get<ResponseBody<'entity_papers_entities__entity_id__papers_get', 200>>(
    `/entities/${id}/papers`,
  )
  return response.data
}

export async function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError<{ detail?: string }>(error)) return fallback
  const detail = error.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}