/**
 * BadgerDoc API Types
 *
 * These types mirror the backend API contract.
 * See docs/api-contract.md for full documentation.
 */

// =============================================================================
// Common Types
// =============================================================================

/**
 * Confidence level for AI-generated data
 */
import type { DuplicateCheckStatus } from '@/shared/api/badgerdoc/types'

export type ConfidenceLevel = 'High' | 'Medium' | 'Low'

// =============================================================================
// Document Types
// =============================================================================

export type DocumentStatus =
  | 'pending_analysis'
  | 'analysis_ready'
  | 'analysis_approved'
  | 'analysis_rejected'
  | 'extraction_ready'
  | 'extraction_approved'
  | 'completed'

export type DocumentType = 'patent' | 'paper' | 'article' | 'report'

export interface DocumentMetadata extends Record<string, unknown> {
  journal?: string
  doi?: string
  sourceUrl?: string
}

export interface Document {
  id: string
  parentDocumentId?: number | null
  title: string
  extension?: string
  type: DocumentType
  status: DocumentStatus
  pdfUrl: string
  thumbnailUrl?: string
  pageCount: number
  metadata: DocumentMetadata
  publicationDate?: string
  authors: string[]
  abstract?: string
  searchQueryId?: string
  createdAt: string
  updatedAt: string
  processedAt?: string
  tags: string[]
  uploadedBy?: string
  duplicateScore?: number
  duplicateStatus?: DuplicateCheckStatus
  duplicateOfId?: string | number | null
}
