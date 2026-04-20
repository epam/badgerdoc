/**
 * Real Documents Adapter
 *
 * Fetches document data from BadgerDoc API.
 */

import type { DocumentsAdapter, DocumentsListParams, DocumentsListResponse } from '../types'
import type { Document } from '@/shared/types/api'
import { apiClient } from '../../client'
import { badgerDocService, transformBadgerDocDocument } from '../../badgerdoc'

export const realDocumentsAdapter: DocumentsAdapter = {
  list: async (params?: DocumentsListParams): Promise<DocumentsListResponse> => {
    // TODO: Implement list from BadgerDoc when available
    const response = await apiClient.get<DocumentsListResponse>('/documents', { params })
    return response.data
  },

  /**
   * Get document by ID from BadgerDoc
   */
  getById: async (id: string): Promise<Document> => {
    const bdDoc = await badgerDocService.getDocument(id)
    return transformBadgerDocDocument(bdDoc)
  },

  updateById: async (id: string, tags: string[], metadata: string): Promise<Document> => {
    const bdDoc = await badgerDocService.updateDocument(id, tags, metadata)
    return transformBadgerDocDocument(bdDoc)
  },

  getPagesById: (id: string): Promise<string[]> => badgerDocService.getDocumentPages(id),

  approve: async (id: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/approve`)
    return response.data
  },

  decline: async (id: string, reason?: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/decline`, { reason })
    return response.data
  },
}
