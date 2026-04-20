import { BadgerDocExtraction, BadgerDocExtractionPage, badgerDocService } from '../../badgerdoc'
import {
  CreateExtractionPageParams,
  CreateExtractionParams,
  ExtractionsAdapter,
  UpdateExtractionParams,
} from '@/shared/api/adapters/types.ts'

export const realExtractionsAdapter: ExtractionsAdapter = {
  getLatestExtraction: async (
    documentId: string,
    tags?: string
  ): Promise<BadgerDocExtractionPage[]> => {
    return badgerDocService.getDocumentExtractionPages(documentId, tags)
  },
  createExtraction: async (params: CreateExtractionParams): Promise<BadgerDocExtraction> =>
    badgerDocService.createExtraction(params),
  createExtractionPage: async (
    params: CreateExtractionPageParams
  ): Promise<BadgerDocExtractionPage> => badgerDocService.createExtractionPage(params),
  updateExtractionPage: async (
    params: CreateExtractionPageParams
  ): Promise<BadgerDocExtractionPage> => badgerDocService.updateExtractionPage(params),
  updateExtraction: async (params: UpdateExtractionParams): Promise<BadgerDocExtraction> => {
    return badgerDocService.updateExtraction(params)
  },
}
