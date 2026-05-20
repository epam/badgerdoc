/**
 * Mock Documents Adapter
 *
 * In-memory document operations with simulated delays.
 */

import type { DocumentsAdapter, DocumentsListParams, DocumentsListResponse } from '../types'
import type { Document, DocumentStatus } from '@/shared/types/api'
import { mockDocuments } from '@/mocks/data/documents'

// Simulated delay for realistic async behavior
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

// In-memory store that can be mutated
const documentsStore = [...mockDocuments]

export const mockDocumentsAdapter: DocumentsAdapter = {
  list: async (params?: DocumentsListParams): Promise<DocumentsListResponse> => {
    await delay(300)

    let filtered = [...documentsStore]

    if (params?.parent_document_id !== undefined) {
      filtered = filtered.filter(
        (d) => String(d.parentDocumentId ?? '') === String(params.parent_document_id)
      )
    }

    if (params?.tags) {
      filtered = filtered.filter((d) => d.tags.includes(params.tags as string))
    }

    if (params?.status) {
      filtered = filtered.filter((d) => d.status === params.status)
    }

    if (params?.search) {
      const query = params.search.toLowerCase()
      filtered = filtered.filter((d) => d.title.toLowerCase().includes(query))
    }

    if (params?.type) {
      filtered = filtered.filter((d) => d.type === params.type)
    }

    // Sorting
    if (params?.sortBy) {
      switch (params.sortBy) {
        case 'newest':
          filtered.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
          break
        case 'oldest':
          filtered.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
          break
      }
    }

    // Pagination
    const pageSize = params?.page_size || params?.limit || 20
    const offset = params?.offset || ((params?.page || 1) - 1) * pageSize
    const limit = pageSize
    const paginated = filtered.slice(offset, offset + limit)

    return {
      count: filtered.length,
      next: offset + limit < filtered.length ? String((params?.page || 1) + 1) : null,
      previous: (params?.page || 1) > 1 ? String((params?.page || 1) - 1) : null,
      results: paginated,
    }
  },

  getById: async (id: string): Promise<Document> => {
    await delay(200)
    const doc = documentsStore.find((d) => d.id === id)
    if (!doc) {
      throw new Error(`Document not found: ${id}`)
    }
    return doc
  },

  updateById: async (id: string, tags: string[], metadata: string): Promise<Document> => {
    await delay(200)
    const doc = documentsStore.find((d) => d.id === id)
    if (!doc) {
      throw new Error(`Document not found: ${id}`)
    }
    doc.tags = tags
    doc.metadata = JSON.parse(metadata.trim())
    return doc
  },

  getPagesById: async (_id: string): Promise<string[]> => {
    await delay(1200)
    return [
      `${__STATIC_ASSETS__}/dzi/2/page_1.dzi`,
      `${__STATIC_ASSETS__}/dzi/2/page_2.dzi`,
      `${__STATIC_ASSETS__}/dzi/2/page_3.dzi`,
    ]
  },

  approve: async (id: string): Promise<Document> => {
    await delay(400)
    const index = documentsStore.findIndex((d) => d.id === id)
    if (index === -1) {
      throw new Error(`Document not found: ${id}`)
    }

    // Determine next status based on current
    let nextStatus: DocumentStatus = 'completed'
    const current = documentsStore[index].status
    if (current === 'analysis_ready' || current === 'pending_analysis') {
      nextStatus = 'extraction_ready'
    } else if (current === 'extraction_ready') {
      nextStatus = 'extraction_approved'
    } else if (current === 'extraction_approved') {
      nextStatus = 'completed'
    }

    documentsStore[index] = {
      ...documentsStore[index],
      status: nextStatus,
      updatedAt: new Date().toISOString(),
    }
    return documentsStore[index]
  },

  decline: async (id: string, _reason?: string): Promise<Document> => {
    await delay(400)
    const index = documentsStore.findIndex((d) => d.id === id)
    if (index === -1) {
      throw new Error(`Document not found: ${id}`)
    }

    documentsStore[index] = {
      ...documentsStore[index],
      status: 'analysis_rejected',
      updatedAt: new Date().toISOString(),
    }
    return documentsStore[index]
  },
}
