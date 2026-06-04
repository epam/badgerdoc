/**
 * API Configuration - Single Source of Truth
 *
 * Centralized configuration for API endpoints, request settings, and feature flags.
 * Supports environment-based configuration for different deployment targets.
 *
 * Environment Variables:
 * - VITE_API_BASE_URL: Backend API base URL (default: http://localhost:3000/api)
 */

export const API_CONFIG = {
  // ==========================================================================
  // Connection Settings
  // ==========================================================================

  /** Base API URL - can be overridden via environment variable */
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api',

  /** Request timeout in milliseconds */
  timeout: 30000,

  /** Maximum number of retry attempts for failed requests */
  maxRetries: 3,

  /** Base delay between retries in milliseconds (exponential backoff) */
  retryDelay: 1000,

  // ==========================================================================
  // Endpoint Paths (for documentation/reference)
  // ==========================================================================

  endpoints: {
    documents: {
      base: '/documents',
      pdf: (id: string) => `/documents/${id}/pdf`,
      analysis: (id: string) => `/documents/${id}/analysis`,
      extraction: (id: string) => `/documents/${id}/extraction`,
    },

    workflow: {
      status: (id: string) => `/documents/${id}/workflow`,
    },
  },

  // ==========================================================================
  // Feature Flags
  // ==========================================================================

  features: {
    /** Enable API request logging in console */
    enableLogging: import.meta.env.DEV,

    /**
     * Per-domain mock overrides
     * Default: uses REAL API (when env var is not set or set to 'false')
     * Set VITE_MOCK_{DOMAIN}=true to use mock data for that domain.
     */
    mockOverrides: {
      documents: import.meta.env.VITE_MOCK_DOCUMENTS === 'true',
      extractions: import.meta.env.VITE_MOCK_EXTRACTIONS === 'true',
      tasks: import.meta.env.VITE_MOCK_TASKS === 'true',
      tags: import.meta.env.VITE_MOCK_TAGS === 'true',
      users: import.meta.env.VITE_MOCK_USERS === 'true',
      uploads: import.meta.env.VITE_MOCK_UPLOADS === 'true',
      workflows: import.meta.env.VITE_MOCK_WORKFLOWS === 'true',
      agentLogs: import.meta.env.VITE_MOCK_AGENT_LOGS === 'true',
    },
  },
} as const
