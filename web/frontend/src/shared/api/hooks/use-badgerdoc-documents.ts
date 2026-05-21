import { useQuery } from '@tanstack/react-query'
import { getApiAdapter } from '../adapters/factory'
import type { DocumentsListParams } from '../adapters/types'

const badgerDocDocumentsKeys = {
  all: ['badgerdoc-documents'] as const,
  lists: () => [...badgerDocDocumentsKeys.all, 'list'] as const,
  list: (params?: DocumentsListParams) => [...badgerDocDocumentsKeys.lists(), params] as const,
}

type UseBadgerDocDocumentsParams = DocumentsListParams

export function useBadgerDocDocuments(params?: UseBadgerDocDocumentsParams) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: badgerDocDocumentsKeys.list(params),
    queryFn: () => adapter.documents.list(params),
  })
}
