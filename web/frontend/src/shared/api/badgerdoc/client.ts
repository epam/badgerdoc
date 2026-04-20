/**
 * BadgerDoc API Client
 *
 * Dedicated Axios client for BadgerDoc API with Bearer token auth (primary)
 * and Basic Auth fallback. Separate from the main apiClient.
 */

import axios from 'axios'
import { getCsrfToken } from '@/helpers/get-csrf-token'
import { getErrorMessageFromResponse } from '@/helpers/get-error-message-from-response'
import { logger } from '@/shared/logger'

// =============================================================================
// CSRF Token Helper
// =============================================================================

// =============================================================================
// Configuration
// =============================================================================

const BADGERDOC_CONFIG = {
  /** BadgerDoc API base URL - uses proxy in dev to bypass CORS */
  baseUrl: import.meta.env.VITE_BADGERDOC_API_URL || '/badgerdoc',

  /** Request timeout in milliseconds */
  timeout: 30000,

  /** Bearer token for authentication (primary method) */
  token: import.meta.env.VITE_BADGERDOC_TOKEN || null,

  /** Basic Auth credentials (used only when explicitly provided) */
  auth: {
    username: import.meta.env.VITE_BADGERDOC_USERNAME || null,
    password: import.meta.env.VITE_BADGERDOC_PASSWORD || null,
  },
} as const

// =============================================================================
// Client Instance
// =============================================================================

/**
 * Axios client configured for BadgerDoc API
 *
 * Authentication priority:
 * 1. Bearer token (if VITE_BADGERDOC_TOKEN is set)
 * 2. Basic Auth (if VITE_BADGERDOC_USERNAME is set)
 * 3. Session cookies (if logged in via Django admin)
 */
export const badgerDocClient = axios.create({
  baseURL: BADGERDOC_CONFIG.baseUrl,
  timeout: BADGERDOC_CONFIG.timeout,
  withCredentials: true, // Send cookies for CSRF
  headers: {
    'Content-Type': 'application/json',
  },
})

// =============================================================================
// Request Interceptor - Auth (Bearer Token, Basic Auth, or Session Cookies)
// =============================================================================

badgerDocClient.interceptors.request.use(
  (config) => {
    // Authentication priority:
    // 1. Bearer token (if VITE_BADGERDOC_TOKEN is set)
    // 2. Basic Auth (if VITE_BADGERDOC_USERNAME is set)
    // 3. Session cookies (no Authorization header, relies on withCredentials: true)
    let authMethod = 'Cookie'

    if (BADGERDOC_CONFIG.token) {
      config.headers.Authorization = `${BADGERDOC_CONFIG.token}`
      authMethod = 'Bearer'
    } else if (BADGERDOC_CONFIG.auth.username) {
      const credentials = `${BADGERDOC_CONFIG.auth.username}:${BADGERDOC_CONFIG.auth.password || ''}`
      config.headers.Authorization = `Basic ${btoa(credentials)}`
      authMethod = 'Basic'
    }
    // If neither token nor username is set, no Authorization header is added
    // The request will use session cookies from Django login (withCredentials: true)

    // CSRF token for state-changing requests
    const csrfMethods = ['post', 'put', 'patch', 'delete']
    if (csrfMethods.includes(config.method?.toLowerCase() || '')) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }

    if (import.meta.env.DEV) {
      logger.debug(`[BadgerDoc] ${config.method?.toUpperCase()} ${config.url} (${authMethod} Auth)`)
    }

    return config
  },
  (error) => Promise.reject(error)
)

// =============================================================================
// Response Interceptor - Error Handling
// =============================================================================

badgerDocClient.interceptors.response.use(
  (response) => {
    // Log successful response in development
    if (import.meta.env.DEV) {
      logger.debug(
        `[BadgerDoc] ${response.config.method?.toUpperCase()} ${response.config.url} -> ${response.status}`
      )
    }
    return response
  },
  (error) => {
    // Log error in development
    if (import.meta.env.DEV) {
      logger.error(`[BadgerDoc] Error:`, error.response?.status, error.message)
    }

    const message = getErrorMessageFromResponse(error)
    const enhancedError = new Error(message)
    ;(enhancedError as Error & { statusCode?: number }).statusCode = error.response?.status

    return Promise.reject(enhancedError)
  }
)
