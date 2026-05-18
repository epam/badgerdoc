/**
 * Mock API Adapter
 *
 * Composes active mock domain adapters into a single ApiAdapter instance.
 * Used by the factory for per-domain switching.
 */

import type { ApiAdapter } from '../types'
import { mockDocumentsAdapter } from './documents'
import { mockTasksAdapter } from './tasks'
import { mockExtractionsAdapter } from './extractions'
import { mockTagsAdapter } from '@/shared/api/adapters/mock/tags.ts'
import { mockWorkflowsAdapter } from './workflows'
import { mockAgentLogsAdapter } from './agent-logs'

export function createMockApiAdapter(): ApiAdapter {
  return {
    documents: mockDocumentsAdapter,
    tasks: mockTasksAdapter,
    extractions: mockExtractionsAdapter,
    tags: mockTagsAdapter,
    workflows: mockWorkflowsAdapter,
    agentLogs: mockAgentLogsAdapter,
  }
}

// Re-export active adapters for direct access if needed.

// Re-export reset functions for testing.
