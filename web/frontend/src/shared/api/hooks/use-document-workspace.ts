/**
 * Document Workspace Hooks
 *
 * React Query hooks for the document workspace page.
 * Combines document data with queue position and highlights.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getApiAdapter } from '../adapters/factory'
import type { Document } from '@/shared/types/api'
import { parsePositiveNumber } from '@/helpers/utils'
import { toast } from 'sonner'

// =============================================================================
// Query Keys
// =============================================================================

const workspaceKeys = {
  all: ['workspace'] as const,
  document: (id: string) => [...workspaceKeys.all, 'document', id] as const,
  pages: (id: string) => [...workspaceKeys.all, 'pages', id] as const,
  highlightsWithTag: (documentId: string, tag: string) =>
    [...workspaceKeys.all, 'highlights', documentId, tag] as const,
}

// =============================================================================
// Document & Queue Hooks
// =============================================================================

/**
 * Fetch document with queue position for workspace
 *
 * @param documentId - Document ID
 *
 * @example
 * const { data, isLoading } = useWorkspaceDocument('doc-1')
 * // data.document - Document details
 * // data.queue - Queue position info
 */
export function useWorkspaceDocument(documentId: string) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workspaceKeys.document(documentId),
    queryFn: (): Promise<Document> => adapter.documents.getById(documentId),
    enabled: !!documentId,
    refetchInterval: (query) => {
      const totalPages = parsePositiveNumber(query.state.data?.metadata?.total_pages)
      return totalPages != null ? false : 2000
    },
  })
}

export function useDocumentPages(documentId: string, expectedPageCount?: number | null) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workspaceKeys.pages(documentId),
    queryFn: (): Promise<string[]> => adapter.documents.getPagesById(documentId),
    enabled: !!documentId,
    // Keep polling while expected page count is missing or incomplete.
    refetchInterval: (query) => {
      const data = query.state.data
      const actualPageCount = data?.length ?? 0

      if (expectedPageCount == null) {
        return 5000
      }

      return actualPageCount !== expectedPageCount ? 5000 : false
    },
  })
}
interface UpdateDocumentMeta {
  id: string
  tags: string[]
  metadata: string
}

export function useUpdateDocumentMeta() {
  const queryClient = useQueryClient()
  const adapter = getApiAdapter()

  return useMutation({
    mutationFn: ({ id, tags, metadata }: UpdateDocumentMeta) =>
      adapter.documents.updateById(id, tags, metadata),
    onSuccess: (updatedDocument) => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.document(updatedDocument.id) })
      toast.success('The document has been updated successfully.')
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to update document'
      toast.error(message)
    },
  })
}
