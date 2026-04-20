import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { authAdapter } from '@/core/auth/adapter'
import { toast } from 'sonner'
import { API_CONFIG } from './config'

// Custom error class for API errors
export class APIError extends Error {
  statusCode?: number
  code?: string
  details?: unknown

  constructor(message: string, statusCode?: number, code?: string, details?: unknown) {
    super(message)
    this.name = 'APIError'
    this.statusCode = statusCode
    this.code = code
    this.details = details
  }
}

// Extend axios config to track retry count
interface RetryConfig extends InternalAxiosRequestConfig {
  _retryCount?: number
  _skipAuthRefresh?: boolean
}

// Calculate exponential backoff delay
function getRetryDelay(retryCount: number): number {
  return Math.min(API_CONFIG.retryDelay * Math.pow(2, retryCount), 30000)
}

// Determine if request should be retried
function shouldRetry(error: AxiosError, config: RetryConfig): boolean {
  const retryCount = config._retryCount || 0

  // Don't retry if max retries exceeded
  if (retryCount >= API_CONFIG.maxRetries) return false

  // Retry on network errors
  if (!error.response) return true

  // Retry on 5xx errors (server errors)
  if (error.response.status >= 500) return true

  // Retry on 429 (rate limited)
  if (error.response.status === 429) return true

  return false
}

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_CONFIG.baseUrl,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await authAdapter.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors and retry logic
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig

    if (!config) {
      return Promise.reject(error)
    }

    // Handle 401 Unauthorized - try token refresh
    if (error.response?.status === 401 && !config._skipAuthRefresh) {
      try {
        await authAdapter.refreshToken()
        config._skipAuthRefresh = true // Prevent infinite loop
        return apiClient.request(config)
      } catch {
        await authAdapter.logout()
        toast.error('Session expired', {
          description: 'Please log in again.',
        })
        return Promise.reject(new APIError('Session expired', 401, 'SESSION_EXPIRED'))
      }
    }

    // Retry logic for transient errors
    if (shouldRetry(error, config)) {
      config._retryCount = (config._retryCount || 0) + 1
      const delay = getRetryDelay(config._retryCount)

      await new Promise((resolve) => setTimeout(resolve, delay))
      return apiClient.request(config)
    }

    // Transform error to APIError
    const apiError = transformError(error)

    // Show toast for user-facing errors
    if (error.response?.status !== 401) {
      showErrorToast(apiError)
    }

    return Promise.reject(apiError)
  }
)

// Transform axios error to APIError
function transformError(error: AxiosError): APIError {
  if (!error.response) {
    return new APIError('Network error. Please check your connection.', undefined, 'NETWORK_ERROR')
  }

  const { status, data } = error.response
  const responseData = data as { message?: string; error?: string; details?: unknown }

  const message = responseData?.message || responseData?.error || getDefaultErrorMessage(status)

  return new APIError(message, status, `HTTP_${status}`, responseData?.details)
}

// Get default error message for status code
function getDefaultErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    400: 'Invalid request. Please check your input.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    408: 'Request timed out. Please try again.',
    422: 'The request could not be processed.',
    429: 'Too many requests. Please wait a moment.',
    500: 'Server error. Please try again later.',
    502: 'Service temporarily unavailable.',
    503: 'Service unavailable. Please try again later.',
  }
  return messages[status] || 'An unexpected error occurred.'
}

// Show error toast notification
function showErrorToast(error: APIError) {
  const shouldShowToast = error.statusCode !== 404 // Don't show toast for 404s

  if (shouldShowToast) {
    toast.error(error.message, {
      description: error.code ? `Error code: ${error.code}` : undefined,
      duration: 5000,
    })
  }
}
