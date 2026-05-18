/**
 * API Adapter Types
 *
 * These interfaces define the contract between the application and the API layer.
 * Both mock and real implementations must conform to these interfaces.
 */

import type { Document, DocumentStatus } from '@/shared/types/api'

import type { AIHint } from '@/shared/types'

import type {
  Task,
  TaskStatus,
  TasksListParams,
  TasksListResponse,
  UpdateTaskRequest,
} from '@/shared/types/tasks'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  AgentLogsResponse,
  BadgerDocExtraction,
  GetAgentLogsParams,
  Tag,
} from '@/shared/api/badgerdoc/types'

// =============================================================================
// Response Types
// =============================================================================

export interface DocumentsListParams {
  status?: DocumentStatus
  search?: string
  type?: string
  sortBy?: 'newest' | 'oldest'
  limit?: number
  offset?: number
}

export interface DocumentsListResponse {
  data: Document[]
  total: number
  hasMore: boolean
}

export interface CreateExtractionParams {
  documentId: string
  status?: string
  comment?: string
  tags?: string[]
}

export interface UpdateExtractionParams {
  extractionId: string | number
  status?: string
  comment?: string
  tags?: string[]
}

export interface CreateExtractionPageParams {
  extractionId: string | number
  pageNumber: number
  content?: string
}

export type WorkflowScope = 'document' | 'page'

/**
 * Raw workflow registry response from GET /workflow-registry/
 */
export interface WorkflowRegistryResponse {
  id: number
  name?: string | null
  created_by: string | null
  event_entity?: string | null
  event_type?: string | null
  document_types?: string[]
  entity_tags?: string[]
  tags?: string[]
  temporal_workflow_type: string
  temporal_queue: string
  is_active: boolean
  trigger: string
  extraction_scope: WorkflowScope[]
  support_prompts?: boolean
  created_at: string
  updated_at: string
}

export interface WorkflowTriggerRequest {
  event_type?: string
  event_entity?: string
  parameters?: Record<string, unknown>
  document_id?: number
  task_id?: number
  extraction_id?: number
  page_number?: number
  scope?: string
}

export interface WorkflowTriggerResponse {
  workflow_id: string
}

export interface WorkflowStatusResponse {
  status: 'In Progress' | 'Finished' | 'Failed' | 'Not Found'
}

// =============================================================================
// Extended AIHint with highlightId for PDF viewer coordination
// =============================================================================

export interface ExtendedAIHint extends AIHint {
  highlightId: string
  reasoning?: string
}

// =============================================================================
// Domain Adapter Interfaces
// =============================================================================

export interface DocumentsAdapter {
  list(params?: DocumentsListParams): Promise<DocumentsListResponse>
  getById(id: string): Promise<Document>
  updateById(id: string, tags: string[], metadata: string): Promise<Document>
  getPagesById(id: string): Promise<string[]>
  approve(id: string): Promise<Document>
  decline(id: string, reason?: string): Promise<Document>
}

export interface ExtractionsAdapter {
  getLatestExtraction(documentId: string, tags?: string): Promise<BadgerDocExtractionPage[]>
  createExtraction(params: CreateExtractionParams): Promise<BadgerDocExtraction>
  createExtractionPage(params: CreateExtractionPageParams): Promise<BadgerDocExtractionPage>
  updateExtractionPage(params: CreateExtractionPageParams): Promise<BadgerDocExtractionPage>
  updateExtraction: (params: UpdateExtractionParams) => Promise<BadgerDocExtraction>
}

export interface TasksAdapter {
  list(params?: TasksListParams): Promise<TasksListResponse>
  getById(taskId: number): Promise<Task>
  updateStatus(taskId: number, request: UpdateTaskRequest): Promise<Task>
  getStatuses(): Promise<TaskStatus[]>
  getNextStatuses(currentStatusId: number): Promise<TaskStatus[]>
}

export interface TagsAdapter {
  getTags(): Promise<Tag[]>
}

export interface WorkflowsAdapter {
  list(
    params?: Partial<{
      event_entity: string
      event_type: string
      is_active: boolean
      trigger: string
      extraction_scope: string
      tags: string[]
    }>
  ): Promise<WorkflowRegistryResponse[]>

  getById(id: number): Promise<WorkflowRegistryResponse>

  trigger(workflowId: number, payload: WorkflowTriggerRequest): Promise<WorkflowTriggerResponse>

  getStatus(workflowId: string): Promise<WorkflowStatusResponse>
}

export interface AgentLogsAdapter {
  getAgentLogs(params: GetAgentLogsParams): Promise<AgentLogsResponse>
}

export interface ApiAdapter {
  documents: DocumentsAdapter
  tasks: TasksAdapter
  extractions: ExtractionsAdapter
  tags: TagsAdapter
  workflows: WorkflowsAdapter
  agentLogs: AgentLogsAdapter
}
