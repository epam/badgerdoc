/**
 * BadgerDoc API Service
 *
 * Service layer wrapping BadgerDoc API endpoints.
 * Provides typed methods for all BadgerDoc operations.
 */

import { badgerDocClient } from './client'
import type { AxiosProgressEvent, AxiosResponse } from 'axios'
import { getFileExtensionFromFileName } from '@/helpers/utils'
import {
  BadgerDocDocument,
  BadgerDocDocumentsResponse,
  BadgerDocExtraction,
  BadgerDocExtractionPage,
  BadgerDocExtractionsResponse,
  BadgerDocExtractionPagesResponse,
  AgentLogsResponse,
  GetAgentLogsParams,
  BadgerDocUploadResponse,
  Tag,
} from './types'
import { User } from '@/shared/types'
import { logger } from '@/shared/logger'
import {
  CreateExtractionPageParams,
  CreateExtractionParams,
  UpdateExtractionParams,
  WorkflowTriggerRequest,
} from '../adapters/types'
import { getApiAdapter } from '../adapters/factory'

// =============================================================================
// API Endpoints
// =============================================================================

const ENDPOINTS = {
  documents: '/documents/',
  document: (id: string | number) => `/document/${id}/`,
  documentPages: (id: string | number) => `/document/${id}/dzi/`,
  documentUpload: '/document/',
  agentLogs: '/agent-log/',
  extractions: '/extractions/',
  tags: '/tags',
  extractionPages: '/extraction-pages/',
  // Direct extraction pages with tags filter
  extractionPageLatest: (documentId: string | number) =>
    `/document/${documentId}/extraction-page/latest/`,
  userData: '/user/me',
  createExtractionPage: '/extraction-page/',
  createExtraction: '/extraction/',
  updateExtraction: (id: string | number) => `/extraction/${id}/`,
} as const

// =============================================================================
// Service Methods
// =============================================================================

/**
 * Parameters for filtering documents
 */
export interface GetDocumentsParams {
  tags?: string
  created_at__gte?: string
  created_at__lte?: string
  /** Filters to documents whose immediate parent is the given document. */
  parent_document_id?: string | number
  page?: number
  page_size?: number
}

interface BadgerDocUserResponse {
  id: number
  username: string
  first_name: string
  last_name: string
  is_admin: true
}

export const badgerDocService = {
  async getCurrentUserData(): Promise<User> {
    const response = await badgerDocClient.get<BadgerDocUserResponse>(ENDPOINTS.userData)

    return {
      id: response.data.id,
      name: `${response.data.first_name} ${response.data.last_name}`,
      role: response.data.is_admin ? 'admin' : 'reviewer',
      username: response.data.username,
    }
  },

  async getTags(): Promise<Tag[]> {
    const response = await badgerDocClient.get<Tag[]>(ENDPOINTS.tags)
    return response.data.sort((a, b) => a.order - b.order)
  },

  /**
   * Get all documents (paginated with optional filters)
   *
   * @param params - Optional filter parameters
   * @returns Paginated list of documents
   */
  async getDocuments(params?: GetDocumentsParams): Promise<BadgerDocDocumentsResponse> {
    const response = await badgerDocClient.get<BadgerDocDocumentsResponse>(ENDPOINTS.documents, {
      params,
    })
    return response.data
  },

  /**
   * Get document information including PDF URL
   *
   * @param documentId - The document ID
   * @returns Document info with Minio file URL
   */
  async getDocument(documentId: string | number): Promise<BadgerDocDocument> {
    const response = await badgerDocClient.get<BadgerDocDocument>(ENDPOINTS.document(documentId))
    return response.data
  },

  async updateDocument(
    documentId: string | number,
    tags: string[],
    metadata: string
  ): Promise<BadgerDocDocument> {
    const formData = new FormData()

    formData.append('tags', JSON.stringify(tags))
    formData.append('metadata', metadata)

    const response = await badgerDocClient.patch<BadgerDocDocument>(
      ENDPOINTS.document(documentId),
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  async getDocumentPages(documentId: string | number): Promise<string[]> {
    const response = await badgerDocClient.get<string[]>(ENDPOINTS.documentPages(documentId))
    return response.data
  },

  async getAgentLogs(params: GetAgentLogsParams): Promise<AgentLogsResponse> {
    const response = await badgerDocClient.get<AgentLogsResponse>(ENDPOINTS.agentLogs, {
      params: {
        document_id: params.documentId,
        ...(params.after ? { after: params.after } : {}),
        ...(params.page ? { page: params.page } : {}),
      },
    })
    return response.data
  },

  /**
   * Get list of extractions for a document
   * Endpoint: GET /extractions/?document_id={id}&tags={tag}
   *
   * @param documentId - The document ID
   * @param tags - Optional tag filter (e.g., 'extraction', 'analysis')
   * @returns List of extractions
   */
  async getExtractions(documentId: string, tags?: string): Promise<BadgerDocExtraction[]> {
    const params: Record<string, string> = { document_id: documentId }
    if (tags) {
      params.tags = tags
    }

    const response = await badgerDocClient.get<
      BadgerDocExtractionsResponse | BadgerDocExtraction[]
    >(ENDPOINTS.extractions, { params })

    // Handle both array and paginated response formats
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.results || []
  },

  /**
   * Get extraction pages for a document filtered by tags
   * Endpoint: GET /document/{document_id}/extraction-page/latest/?tags={tag}
   *
   * @param documentId - The document ID
   * @param tags - Tag filter: 'analysis' or 'extraction'
   * @returns Extraction pages with blocks
   */
  async getDocumentExtractionPages(
    documentId: string,
    tags?: string,
    status: string = 'Completed'
  ): Promise<BadgerDocExtractionPage[]> {
    logger.debug(`[BadgerDoc] getDocumentExtractionPages(${documentId}, ${tags})`)

    const response = await badgerDocClient.get<BadgerDocExtractionPagesResponse>(
      ENDPOINTS.extractionPageLatest(documentId),
      { params: { tags, status } }
    )

    const pages = response.data.results || []
    logger.debug(`[BadgerDoc] Got ${pages.length} pages`)
    return pages
  },

  /**
   * Create a new extraction for a document
   * Endpoint: POST /extractions
   *
   * @param params - Extraction creation parameters
   * @param params.documentId - The document ID
   * @param params.status - Optional extraction status
   * @param params.comment - Optional comment for the extraction
   * @param params.tags - Optional list of tags
   * @returns Created extraction with details
   */
  async createExtraction(params: CreateExtractionParams): Promise<BadgerDocExtraction> {
    const response = await badgerDocClient.post<BadgerDocExtraction>(ENDPOINTS.createExtraction, {
      document_id: Number(params.documentId),
      status: params.status || '',
      comment: params.comment || '',
      tags: params.tags || [],
    })

    return response.data
  },

  /**
   * Create a new extraction page for a specific extraction
   * Endpoint: POST /extractions
   *
   * @param params - Extraction page creation parameters
   * @param params.extractionId - The extraction ID
   * @param params.pageNumber - The page number within the extraction
   * @param params.content - Optional page content
   * @returns Created extraction page with details
   */
  async createExtractionPage(params: CreateExtractionPageParams): Promise<BadgerDocExtractionPage> {
    const response = await badgerDocClient.post<BadgerDocExtractionPage>(
      ENDPOINTS.createExtractionPage,
      {
        extraction_id: Number(params.extractionId),
        page_number: params.pageNumber,
        content: params.content || '',
      }
    )

    return response.data
  },

  /**
   * Create a new extraction page for a specific extraction
   * Endpoint: POST /extractions
   *
   * @param params - Extraction page creation parameters
   * @param params.extractionId - The extraction ID
   * @param params.pageNumber - The page number within the extraction
   * @param params.content - Optional page content
   * @returns Created extraction page with details
   */
  async updateExtractionPage(params: CreateExtractionPageParams): Promise<BadgerDocExtractionPage> {
    const response = await badgerDocClient.patch<BadgerDocExtractionPage>(
      ENDPOINTS.createExtractionPage,
      {
        extraction_id: Number(params.extractionId),
        page_number: params.pageNumber,
        content: params.content || '',
      }
    )

    return response.data
  },

  /**
   * Update an existing extraction
   * Endpoint: PATCH /extractions/{extraction_id}
   *
   * @param params - Extraction update parameters
   * @param params.extractionId - The extraction ID
   * @param params.status - Optional updated status
   * @param params.comment - Optional updated comment
   * @param params.tags - Optional list of tags
   * @returns Updated extraction with details
   */
  async updateExtraction(params: UpdateExtractionParams): Promise<BadgerDocExtraction> {
    const { extractionId, ...updateFields } = params

    const response = await badgerDocClient.patch<BadgerDocExtraction>(
      ENDPOINTS.updateExtraction(extractionId),
      updateFields
    )

    return response.data
  },

  /**
   * Check extraction status for a document
   * Used for polling to determine available tabs/stages
   *
   * @param documentId - The document ID
   * @returns All extractions for the document with their status
   */
  async checkExtractionStatus(documentId: string): Promise<BadgerDocExtraction[]> {
    return this.getExtractions(documentId)
  },

  /**
   * Get extractions for a task filtered by tag
   * Endpoint: GET /extractions/?task_id={id}&tags={tag}
   *
   * @param taskId - The task ID
   * @param tags - Tag filter (e.g., 'ocr', 'relevance-check')
   * @returns List of extractions with timestamps
   */
  async getExtractionsByTaskAndTag(taskId: number, tags: string): Promise<BadgerDocExtraction[]> {
    const params: Record<string, string | number> = {
      task_id: taskId,
      tags,
    }

    const response = await badgerDocClient.get<
      BadgerDocExtractionsResponse | BadgerDocExtraction[]
    >(ENDPOINTS.extractions, { params })

    // Handle both array and paginated response formats
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.results || []
  },

  /**
   * Get extraction pages by extraction ID
   * Endpoint: GET /extraction-pages/?extraction_id={id}
   *
   * @param extractionId - The extraction ID
   * @returns Extraction pages with blocks
   */
  async getExtractionPagesByExtractionId(extractionId: number): Promise<BadgerDocExtractionPage[]> {
    logger.debug(`[BadgerDoc] getExtractionPagesByExtractionId(${extractionId})`)

    const response = await badgerDocClient.get<BadgerDocExtractionPagesResponse>(
      ENDPOINTS.extractionPages,
      { params: { extraction_id: extractionId } }
    )

    const pages = response.data.results || []
    logger.debug(`[BadgerDoc] Got ${pages.length} pages for extraction ${extractionId}`)
    return pages
  },

  /**
   * Upload a document to BadgerDoc
   * Endpoint: POST /document/
   *
   * Throws an error (AxiosError) if the request fails.
   * Access error response body via: error.response?.data
   * For 400 validation errors: error.response?.data?.file contains error messages
   *
   * @param file - PDF file to upload
   * @param tags - Tags to apply to the document
   * @param metadata
   * @param onUploadProgress - Optional callback for upload progress
   * @returns Upload response with document ID on success (201)
   * @throws AxiosError with response body containing validation errors
   */
  async uploadDocument(
    file: File,
    tags: string[] = [],
    metadata: string,
    onUploadProgress?: (event: AxiosProgressEvent) => void
  ): Promise<AxiosResponse<BadgerDocUploadResponse>> {
    const extension = getFileExtensionFromFileName(file.name)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('extension', extension)
    if (tags?.length) {
      formData.append('tags', JSON.stringify(tags))
    }
    if (metadata?.length) {
      formData.append('metadata', metadata)
    }

    return badgerDocClient.post<BadgerDocUploadResponse>(ENDPOINTS.documentUpload, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
      timeout: 120000, // 2 minutes for large files
    })
  },

  async getWorkflows(params?: {
    event_entity?: string
    event_type?: string
    is_active?: boolean
    trigger?: string
    extraction_scope?: string
    tags?: string[]
  }) {
    const adapter = getApiAdapter()
    const response = await adapter.workflows.list(params)
    return response.map((r) => ({
      id: r.id,
      name: r.name ?? '',
      tags: r.tags ?? [],
      createdBy: r.created_by,
      eventEntity: r.event_entity || null,
      eventType: r.event_type || null,
      documentTypes: r.document_types || [],
      entityTags: r.entity_tags || [],
      temporalWorkflowType: r.temporal_workflow_type,
      temporalQueue: r.temporal_queue,
      isActive: !!r.is_active,
      trigger: r.trigger,
      extractionScope: r.extraction_scope || [],
      supportPrompts: !!r.support_prompts,
      createdAt: r.created_at,
      updatedAt: r.updated_at,
    }))
  },

  async getWorkflow(id: number) {
    const adapter = getApiAdapter()
    const r = await adapter.workflows.getById(id)
    return {
      id: r.id,
      name: r.name ?? '',
      createdBy: r.created_by,
      eventEntity: r.event_entity || null,
      eventType: r.event_type || null,
      documentTypes: r.document_types || [],
      entityTags: r.entity_tags || [],
      temporalWorkflowType: r.temporal_workflow_type,
      temporalQueue: r.temporal_queue,
      isActive: !!r.is_active,
      trigger: r.trigger,
      extractionScope: r.extraction_scope || [],
      supportPrompts: !!r.support_prompts,
      createdAt: r.created_at,
      updatedAt: r.updated_at,
    }
  },

  async triggerWorkflow(id: number, payload: Record<string, unknown>) {
    const adapter = getApiAdapter()
    const res = await adapter.workflows.trigger(id, payload as WorkflowTriggerRequest)
    return res
  },

  async getWorkflowStatus(workflowId: string) {
    const adapter = getApiAdapter()
    const res = await adapter.workflows.getStatus(workflowId)
    return res
  },
}
