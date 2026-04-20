/**
 * Tasks API Types
 *
 * TypeScript types for the BadgerDoc Tasks API integration.
 * These types map to the backend API endpoints:
 * - GET /badgerdoc/tasks/
 * - GET /badgerdoc/task/{id}/details/
 * - GET /badgerdoc/task/status/
 * - GET /badgerdoc/task/status/next/{id}/
 * - PATCH /badgerdoc/task/{id}/
 */

// Re-export workflow config for convenience
export { STATUS_IDS } from '@/config/workflow'

// Local imports for use in helper functions below
import { STATUS_IDS } from '@/config/workflow'

// =============================================================================
// Task Status
// =============================================================================

export interface TaskStatus {
  id: number
  name: string
  order: number
}

// =============================================================================
// Task Document
// =============================================================================

export interface TaskDocument {
  id: number
  file: string
  metadata: Record<string, unknown> | null
  tags: string[] | null
}

// =============================================================================
// Task Extraction
// =============================================================================

export interface TaskExtraction {
  id: number
  status: string
  comment: string | null
  tags: string[]
}

// =============================================================================
// Task
// =============================================================================

export interface Task {
  id: number
  user: number
  status: TaskStatus
  document: TaskDocument
  extractions: TaskExtraction[]
  created_at: string
  updated_at: string
}

// =============================================================================
// API Request/Response Types
// =============================================================================

export interface TasksListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Task[]
}

export interface TasksListParams {
  status_id?: number
  user_id?: number
  created_at__gte?: string
  created_at__lte?: string
  updated_at__gte?: string
  updated_at__lte?: string
  page?: number
  page_size?: number
}

export interface TasksQueueParams extends TasksListParams {
  currentTaskId: number
}

export interface UpdateTaskRequest {
  status: number
  /** IDs of approved extractions to include when updating task status */
  extractions?: number[]
}

// =============================================================================
// Helpers for UI mapping
// =============================================================================

/** Map task status to action label for dashboard/tasks list */
export function getTaskActionLabel(statusId: number): string {
  switch (statusId) {
    case STATUS_IDS.CURATED:
      return 'View'
    case STATUS_IDS.REJECT:
    case STATUS_IDS.REJECT_DUPLICATE:
    case STATUS_IDS.REJECT_WITH_REASON:
      return 'View'
    default:
      return 'Review'
  }
}
