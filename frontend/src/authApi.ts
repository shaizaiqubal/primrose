import axios from 'axios'
import type { components } from './api-schema'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

export type Credentials = components['schemas']['UserCreate']
export type EmailRequest = components['schemas']['EmailRequest']

export type LoginResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

const verificationRequests = new Map<string, Promise<void>>()

export async function registerAccount(credentials: Credentials) {
  const response = await api.post<components['schemas']['UserResponse']>(
    '/auth/register',
    credentials,
  )
  return response.data
}

export async function sendVerificationEmail(request: EmailRequest) {
  await api.post('/auth/send_email', request)
}

export async function signIn(credentials: Credentials) {
  const response = await api.post<LoginResponse>('/auth/login', credentials)
  return response.data
}

export async function verifyEmail(token: string) {
  await api.get('/auth/verify-email', { params: { token } })
}

export function verifyEmailOnce(token: string) {
  const existingRequest = verificationRequests.get(token)
  if (existingRequest) return existingRequest

  const request = verifyEmail(token)
  verificationRequests.set(token, request)
  const clearRequest = () => {
    if (verificationRequests.get(token) === request) verificationRequests.delete(token)
  }
  void request.then(clearRequest, clearRequest)
  return request
}

export function getApiError(error: unknown, fallback: string) {
  if (!axios.isAxiosError<{ detail?: string }>(error)) return fallback
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Check the email and password fields, then try again.'
  return fallback
}