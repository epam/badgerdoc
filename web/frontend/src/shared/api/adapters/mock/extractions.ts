import { delay } from 'msw'
import { ExtractionsAdapter } from '@/shared/api/adapters/types'
import { createExtractionMock, extractionMock, extractionPageMock } from '@/mocks/data/extractions'
import { BadgerDocExtraction, BadgerDocExtractionPage } from '@/shared/api/badgerdoc'

export const mockExtractionsAdapter: ExtractionsAdapter = {
  getLatestExtraction: async (
    _documentId: string,
    _tags?: string
  ): Promise<BadgerDocExtractionPage[]> => {
    void delay(200)
    return extractionMock
  },
  createExtraction: async (): Promise<BadgerDocExtraction> => {
    void delay(200)
    return createExtractionMock
  },
  createExtractionPage: async (): Promise<BadgerDocExtractionPage> => {
    void delay(200)
    return extractionPageMock
  },
  updateExtractionPage: async (): Promise<BadgerDocExtractionPage> => {
    void delay(200)
    return extractionPageMock
  },
  updateExtraction: async (): Promise<BadgerDocExtraction> => {
    void delay(200)
    return createExtractionMock
  },
}
