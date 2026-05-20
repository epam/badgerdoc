/**
 * Real Documents Adapter
 *
 * Fetches document data from BadgerDoc API.
 */

import type { DocumentsAdapter, DocumentsListParams, DocumentsListResponse } from '../types'
import type { Document } from '@/shared/types/api'
import { apiClient } from '../../client'
import { badgerDocClient } from '../../badgerdoc/client'
import type {
  BadgerDocDocument,
  BadgerDocDocumentsResponse,
  PageSource,
} from '../../badgerdoc/types'
import { transformBadgerDocDocument } from '../../badgerdoc'
import { logger } from '@/shared/logger'

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

async function fetchDziPages(id: string): Promise<string[]> {
  try {
    const response = await badgerDocClient.get<string[]>(`/document/${id}/dzi/`)
    return response.data ?? []
  } catch (error) {
    logger.warn('Failed to fetch DZI page list, will try PNG fallback', error)
    return []
  }
}

async function fetchPngRenditionPages(id: string): Promise<PageSource[]> {
  const response = await badgerDocClient.get<BadgerDocDocument[]>(`/document/${id}/renditions/`)
  const renditions = response.data ?? []
  return renditions
    .filter((doc) => Boolean(doc.file))
    .sort((a, b) => {
      const pageA = (a.metadata?.page as number | undefined) ?? 0
      const pageB = (b.metadata?.page as number | undefined) ?? 0
      return pageA - pageB
    })
    .map((doc) => ({ type: 'image', url: doc.file }))
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

  /**
   * Returns viewer page sources. Tiled (DZI) sources are primary; if the API
   * returns no DZI assets, PNG renditions are returned as a static fallback so
   * the document is still viewable read-only.
   */
  getPagesById: async (id: string): Promise<PageSource[]> => {
    const dziUrls = await fetchDziPages(id)
    if (dziUrls.length > 0) {
      return dziUrls.map((url) => ({ type: 'dzi', url }))
    }
    return fetchPngRenditionPages(id)
  },

  getPngPagesById: (id: string): Promise<PageSource[]> => fetchPngRenditionPages(id),

  approve: async (id: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/approve`)
    return response.data
  },

  decline: async (id: string, reason?: string): Promise<Document> => {
    const response = await apiClient.post<Document>(`/documents/${id}/decline`, { reason })
    return response.data
  },
}
