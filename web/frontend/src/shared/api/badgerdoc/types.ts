/**
 * BadgerDoc API Types
 *
 * Type definitions for the BadgerDoc backend API responses.
 * These types represent the raw data structure from the API before transformation.
 */

// =============================================================================
// Block Types
// =============================================================================

/**
 * Approval status for a block
 */
export interface BadgerDocApprovalStatus {
  user_id: string
  approved: boolean
  timestamp: string
}

/**
 * Parsed extraction response for tables
 *
 * Can be either:
 * 1. Standard format: { columns: string[], rows: Array<Record<string, unknown>> }
 * 2. Column-major stringified JSON: string containing { "0": { "0": "Header", "1": "Value" }, ... }
 *
 * The column-major format is returned by BadgerDoc API where:
 * - Top-level keys are column indices
 * - Row 0 contains headers
 * - Remaining rows contain data
 */
export type BadgerDocTableData =
  | { columns: string[]; rows: Array<Record<string, unknown>> }
  | Record<string, Record<string, string | null>>
  | string

/**
 * Parsed extraction response containing data and text
 */
export interface BadgerDocExtractionParsed {
  data: BadgerDocTableData | null
  text: string
}

/**
 * Block types returned from BadgerDoc
 */
export type BadgerDocBlockType = 'table' | 'paragraph' | 'diagram' | 'figure' | 'header' | string

/**
 * A single block/region identified in the document
 * Bbox format: [x1, y1, x2, y2] - corner coordinates in normalized 0-1 range
 */
export interface BadgerDocBlock {
  bbox: [number, number, number, number]
  type: BadgerDocBlockType
  approval_status: BadgerDocApprovalStatus
  extraction_response: string | null
  extraction_response_parsed: BadgerDocExtractionParsed | null
}

/**
 * Extraction page containing OCR results
 * Supports both direct ocr and content.ocr structures
 */
export interface BadgerDocExtractionPage {
  id?: number
  extraction_id?: number
  page_number: number
  content?: string
  created_at?: string
  updated_at?: string
}

export interface OverlayBox {
  id: string
  x: number
  y: number
  width: number
  height: number
  page: number
}

/**
 * Source descriptor for a single page in the document viewer.
 *
 * `dzi` is the primary tiled-rendering mode (Deep Zoom Image XML + PNG tiles).
 * `image` is the PNG fallback used when tiled assets are unavailable; the
 * viewer renders read-only without interactive overlays in this mode.
 */
export type PageSource = { type: 'dzi'; url: string } | { type: 'image'; url: string }

// =============================================================================
// Document Types
// =============================================================================

/**
 * Duplicate check status for HITL workflow
 */
export type DuplicateCheckStatus = 'pending' | 'confirmed_unique' | 'confirmed_duplicate'

/**
 * Document information from BadgerDoc
 * From GET /document/{id} or /documents/ list
 */
export interface BadgerDocDocument {
  id: number | string
  uploaded_by?: string
  parent_document_id?: number | null
  file: string // Minio URL to PDF (note: 'file' not 'file_url')
  extension?: string
  metadata?: Record<string, unknown> | null
  tags?: string[] | null
  created_at?: string
  updated_at?: string
  // Legacy field name support
  file_url?: string
  name?: string
  status?: string
  // Duplicate check fields
  duplicate_score?: number // 0-100, percentage match with existing document
  duplicate_status?: DuplicateCheckStatus
  duplicate_of_id?: number | string | null // ID of the document this is a duplicate of
}

/**
 * Paginated documents list response from GET /documents/
 */
export interface BadgerDocDocumentsResponse {
  count: number
  next: string | null
  previous: string | null
  results: BadgerDocDocument[]
}

// =============================================================================
// Extraction Types
// =============================================================================

/**
 * Extraction status values (API returns capitalized)
 */
export type BadgerDocExtractionStatus = 'Pending' | 'Processing' | 'Completed' | 'Failed' | string

/**
 * Extraction metadata from GET /extractions/
 */
export interface BadgerDocExtraction {
  id: number | string
  document_id: number | string
  created_by?: string
  status: BadgerDocExtractionStatus
  temporal_job_id?: string | null
  comment?: string
  tags: string[]
  created_at?: string
  updated_at?: string
}

/**
 * Response from GET /extractions/
 * Format: { count, next, previous, results }
 */
export interface BadgerDocExtractionsResponse {
  count: number
  next: string | null
  previous: string | null
  results: BadgerDocExtraction[]
}

/**
 * Response from GET /extraction-pages/
 * Format: { count, next, previous, results }
 */
export interface BadgerDocExtractionPagesResponse {
  count: number
  next: string | null
  previous: string | null
  results: BadgerDocExtractionPage[]
}

// =============================================================================
// Agent Log Types
// =============================================================================

export type AgentLogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

export interface AgentLogPayload {
  message?: string
  markdown?: string
  code?: string
  document?: number | null
  workflow_params?: unknown
}

export interface AgentLog {
  id: number | string
  document: number
  task?: number | string | null
  level: AgentLogLevel
  source?: string | null
  log: AgentLogPayload
  created_at: string
}

export interface GetAgentLogsParams {
  documentId: string | number
  after?: string
  page?: number
}

/**
 * Response from GET /agent-log/
 * Format: { count, next, previous, results }
 */
export interface AgentLogsResponse {
  count: number
  next: string | null
  previous: string | null
  results: AgentLog[]
}

// =============================================================================
// Upload Types
// =============================================================================

/**
 * Response from POST /document/
 * Returned after successful document upload
 */
export interface BadgerDocUploadResponse {
  id: number
  uploaded_by: string
  file: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface Tag {
  order: number
  literal: string
  tag: string
}
