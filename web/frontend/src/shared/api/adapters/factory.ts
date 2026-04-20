/**
 * API Adapter Factory
 *
 * Central switching point for mock vs real API implementations.
 * Supports per-domain configuration via VITE_MOCK_{DOMAIN} environment variables.
 * Note: VITE_USE_MOCK_FALLBACK is not applied here; switching is driven by per-domain flags.
 */

import type { ApiAdapter } from './types'
import { API_CONFIG } from '../config'
import { createMockApiAdapter } from './mock'
import { createRealApiAdapter } from './real'
import { logger } from '@/shared/logger'

// Singleton instance
let adapterInstance: ApiAdapter | null = null

/**
 * Get the API adapter instance
 *
 * Creates a hybrid adapter where each domain can independently use
 * mock or real implementation based on VITE_MOCK_{DOMAIN} env variables.
 * Instance is cached for performance.
 */
export function getApiAdapter(): ApiAdapter {
  if (!adapterInstance) {
    const o = API_CONFIG.features.mockOverrides
    const mockAdapter = createMockApiAdapter()
    const realAdapter = createRealApiAdapter()

    adapterInstance = {
      documents: o.documents ? mockAdapter.documents : realAdapter.documents,
      tasks: o.tasks ? mockAdapter.tasks : realAdapter.tasks,
      extractions: o.extractions ? mockAdapter.extractions : realAdapter.extractions,
      tags: o.tags ? mockAdapter.tags : realAdapter.tags,
      workflows: o.workflows ? mockAdapter.workflows : realAdapter.workflows,
    }

    // Log which adapters are using real vs mock
    if (API_CONFIG.features.enableLogging) {
      const activeDomains = {
        documents: o.documents,
        tasks: o.tasks,
        extractions: o.extractions,
        tags: o.tags,
      }
      logger.debug(
        '[API] Adapter configuration:',
        Object.entries(activeDomains)
          .map(([k, v]) => `${k}: ${v ? 'mock' : 'REAL'}`)
          .join(', ')
      )
    }
  }
  return adapterInstance
}
