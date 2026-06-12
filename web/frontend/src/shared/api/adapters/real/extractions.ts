import type { BadgerDocExtraction, BadgerDocExtractionPage } from '../../badgerdoc'
import type { BadgerDocExtractionPagesResponse } from '../../badgerdoc/types'
import { badgerDocClient } from '../../badgerdoc/client'
import {
  CreateExtractionPageParams,
  CreateExtractionParams,
  ExtractionsAdapter,
  UpdateExtractionParams,
} from '@/shared/api/adapters/types'

export const realExtractionsAdapter: ExtractionsAdapter = {
  getLatestExtraction: async (
    documentId: string,
    tags?: string
  ): Promise<BadgerDocExtractionPage[]> => {
    const response = await badgerDocClient.get<BadgerDocExtractionPagesResponse>(
      `/document/${documentId}/extraction-page/latest/`,
      { params: { tags, status: 'Completed' } }
    )
    return response.data.results || []
  },
  createExtraction: async (params: CreateExtractionParams): Promise<BadgerDocExtraction> => {
    const response = await badgerDocClient.post<BadgerDocExtraction>(`/extraction/`, {
      document_id: Number(params.documentId),
      status: params.status || '',
      comment: params.comment || '',
      tags: params.tags || [],
    })
    return response.data
  },
  createExtractionPage: async (
    params: CreateExtractionPageParams
  ): Promise<BadgerDocExtractionPage> => {
    const response = await badgerDocClient.post<BadgerDocExtractionPage>(`/extraction-page/`, {
      extraction_id: Number(params.extractionId),
      page_number: params.pageNumber,
      content: params.content || '',
    })
    return response.data
  },
  updateExtractionPage: async (
    params: CreateExtractionPageParams
  ): Promise<BadgerDocExtractionPage> => {
    const response = await badgerDocClient.patch<BadgerDocExtractionPage>(`/extraction-page/`, {
      extraction_id: Number(params.extractionId),
      page_number: params.pageNumber,
      content: params.content || '',
    })
    return response.data
  },
  updateExtraction: async (params: UpdateExtractionParams): Promise<BadgerDocExtraction> => {
    const { extractionId, ...updateFields } = params
    const response = await badgerDocClient.patch<BadgerDocExtraction>(
      `/extraction/${extractionId}/`,
      updateFields
    )
    return response.data
  },
}
