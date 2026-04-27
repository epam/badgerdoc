/**
 * Document Workspace Hooks
 *
 * React Query hooks for the document workspace page.
 * Combines document data with queue position and highlights.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getApiAdapter } from '../adapters/factory'
import type { Document } from '@/shared/types/api'
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
  })
}

export function useDocumentPages(documentId: string) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workspaceKeys.pages(documentId),
    queryFn: (): Promise<string[]> => adapter.documents.getPagesById(documentId),
    enabled: !!documentId,
        //if responce is [], let's refetch after 10s
    // TODO: remove this heuristic once backend provides document processing status
    // currently using pages.length === 0 to detect "processing"
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.length === 0 ? 10000 : false
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
