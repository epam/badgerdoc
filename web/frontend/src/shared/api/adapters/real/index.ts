/**
 * Real API Adapter
 *
 * Composes active real domain adapters into a single ApiAdapter instance.
 * Used by the factory for per-domain switching.
 */

import type { ApiAdapter } from '../types'
import { realDocumentsAdapter } from './documents'
import { realTasksAdapter } from './tasks'
import { realExtractionsAdapter } from './extractions'
import { realTagsAdapter } from '@/shared/api/adapters/real/tags.ts'
import { realUsersAdapter } from './users'
import { realUploadsAdapter } from './uploads'
import { realWorkflowsAdapter } from './workflows'

export function createRealApiAdapter(): ApiAdapter {
  return {
    documents: realDocumentsAdapter,
    tasks: realTasksAdapter,
    extractions: realExtractionsAdapter,
    tags: realTagsAdapter,
    users: realUsersAdapter,
    uploads: realUploadsAdapter,
    workflows: realWorkflowsAdapter,
  }
}

// Re-export active adapters for direct access if needed.
