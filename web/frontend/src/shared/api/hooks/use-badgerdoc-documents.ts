import { useQuery } from '@tanstack/react-query'
import { badgerDocService, type GetDocumentsParams } from '../badgerdoc/service'
import type { BadgerDocDocumentsResponse, DuplicateCheckStatus } from '../badgerdoc/types'

const badgerDocDocumentsKeys = {
  all: ['badgerdoc-documents'] as const,
  lists: () => [...badgerDocDocumentsKeys.all, 'list'] as const,
  list: (params?: GetDocumentsParams) => [...badgerDocDocumentsKeys.lists(), params] as const,
}

interface UseBadgerDocDocumentsParams {
  tags?: string
  created_at__gte?: string
  created_at__lte?: string
  page?: number
  page_size?: number
}

/**
 * Mock duplicate check data for UI testing.
 * Maps document ID to duplicate info.
 * Remove this when the backend supports duplicate checking.
 */
const MOCK_DUPLICATES: Record<
  string,
  { score: number; status: DuplicateCheckStatus; duplicateOfId: number }
> = {
  // Document ID 6 - first document in list (high similarity)
  '6': { score: 92, status: 'pending', duplicateOfId: 1 },
  // Additional test documents with duplicates
  '2': { score: 85, status: 'pending', duplicateOfId: 1 },
  '4': { score: 72, status: 'pending', duplicateOfId: 3 },
}

/**
 * Inject mock duplicate check data for UI testing.
 * Remove this when the backend supports duplicate checking.
 */
function injectMockDuplicateData(response: BadgerDocDocumentsResponse): BadgerDocDocumentsResponse {
  // Only inject mock data in development mode
  if (import.meta.env.PROD) {
    return response
  }

  return {
    ...response,
    results: response.results.map((doc) => {
      const docId = String(doc.id)
      const mockData = MOCK_DUPLICATES[docId]
      if (mockData && !doc.duplicate_status) {
        return {
          ...doc,
          duplicate_score: mockData.score,
          duplicate_status: mockData.status,
          duplicate_of_id: mockData.duplicateOfId,
        }
      }
      return doc
    }),
  }
}

export function useBadgerDocDocuments(params?: UseBadgerDocDocumentsParams) {
  return useQuery({
    queryKey: badgerDocDocumentsKeys.list(params),
    queryFn: async () => {
      const response = await badgerDocService.getDocuments(params)
      return injectMockDuplicateData(response)
    },
  })
}
