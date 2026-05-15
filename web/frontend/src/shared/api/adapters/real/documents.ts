/**
 * Real Documents Adapter
 *
 * Fetches document data from BadgerDoc API.
 */

import type { DocumentsAdapter, DocumentsListParams, DocumentsListResponse } from '../types'
import type { Document } from '@/shared/types/api'
import { apiClient } from '../../client'
import { badgerDocClient } from '../../badgerdoc/client'
import type { BadgerDocDocument, BadgerDocDocumentsResponse } from '../../badgerdoc/types'
import { transformBadgerDocDocument } from '../../badgerdoc'

function toDocumentsListResponse(response: BadgerDocDocumentsResponse): DocumentsListResponse {
  return {
    count: response.count,
    next: response.next,
    previous: response.previous,
    results: response.results.map((document) => transformBadgerDocDocument(document)),
  }
}

async function getBadgerDocDocument(id: string | number): Promise<BadgerDocDocument> {
  const response = await badgerDocClient.get<BadgerDocDocument>(`/document/${id}/`)
  return response.data
}

export const realDocumentsAdapter: DocumentsAdapter = {
  list: async (params?: DocumentsListParams): Promise<DocumentsListResponse> => {
    const response = await badgerDocClient.get<BadgerDocDocumentsResponse>('/documents/', {
      params,
    })
    return toDocumentsListResponse(response.data)
  },

  /**
   * Get document by ID from BadgerDoc
   */
  getById: async (id: string): Promise<Document> => {
    const bdDoc = await getBadgerDocDocument(id)
    return transformBadgerDocDocument(bdDoc)
  },

  updateById: async (id: string, tags: string[], metadata: string): Promise<Document> => {
    const formData = new FormData()

    formData.append('tags', JSON.stringify(tags))
    formData.append('metadata', metadata)

    const response = await badgerDocClient.patch<BadgerDocDocument>(`/document/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const bdDoc = response.data
    return transformBadgerDocDocument(bdDoc)
  },

  getPagesById: async (id: string): Promise<string[]> => {
    const response = await badgerDocClient.get<string[]>(`/document/${id}/dzi/`)
    return response.data
  },

  approve: async (id: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/approve`)
    return response.data
  },

  decline: async (id: string, reason?: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/decline`, { reason })
    return response.data
  },
}
