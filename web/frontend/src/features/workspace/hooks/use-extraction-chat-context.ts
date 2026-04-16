import { useCallback, useMemo, useState } from 'react'
import type { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  EMPTY_EXTRACTION_CONTEXT,
  addDocumentToContext,
  buildExtractionContextPayload,
  clearExtractionContext,
  normalizeExtractionContext,
  removeBlockFromContext,
  removeDeletedBlockFromContext,
  removePageFromContext,
  toggleBlockInContext,
  togglePageInContext,
  type ExtractionContextBlock,
} from '@/features/workspace/helpers/extraction-chat-context'

interface UseExtractionChatContextParams {
  documentId: string
  extractionPages?: BadgerDocExtractionPage[]
  activeTag?: string
}

export function useExtractionChatContext({
  documentId,
  extractionPages,
  activeTag,
}: UseExtractionChatContextParams) {
  const extractionId = extractionPages?.[0]?.extraction_id ?? null
  const contextKey = `${documentId}:${extractionId ?? 'none'}:${activeTag ?? 'overview'}`
  const [contextState, setContextState] = useState({
    key: contextKey,
    context: EMPTY_EXTRACTION_CONTEXT,
  })

  if (contextState.key !== contextKey) {
    setContextState({
      key: contextKey,
      context: EMPTY_EXTRACTION_CONTEXT,
    })
  }

  const addWholeDocument = useCallback(() => {
    setContextState((prev) => ({ ...prev, context: addDocumentToContext() }))
  }, [])

  const removePage = useCallback((pageNumber: number) => {
    setContextState((prev) => ({
      ...prev,
      context: removePageFromContext(prev.context, pageNumber),
    }))
  }, [])

  const togglePage = useCallback((pageNumber: number) => {
    setContextState((prev) => ({
      ...prev,
      context: togglePageInContext(prev.context, pageNumber),
    }))
  }, [])

  const toggleBlock = useCallback((block: ExtractionContextBlock) => {
    setContextState((prev) => ({
      ...prev,
      context: toggleBlockInContext(prev.context, block),
    }))
  }, [])

  const removeBlock = useCallback((blockId: string) => {
    setContextState((prev) => ({
      ...prev,
      context: removeBlockFromContext(prev.context, blockId),
    }))
  }, [])

  const clearAll = useCallback(() => {
    setContextState((prev) => ({ ...prev, context: clearExtractionContext() }))
  }, [])

  const removeDeletedBlock = useCallback((blockId: string) => {
    setContextState((prev) => ({
      ...prev,
      context: removeDeletedBlockFromContext(prev.context, blockId),
    }))
  }, [])

  const normalizedContext = useMemo(
    () => normalizeExtractionContext(contextState.context),
    [contextState.context]
  )
  const payload = useMemo(
    () =>
      buildExtractionContextPayload({
        context: normalizedContext,
        documentId: Number(documentId),
        extractionId,
      }),
    [documentId, extractionId, normalizedContext]
  )

  return {
    context: normalizedContext,
    contextPayload: payload,
    extractionId,
    hasContext: normalizedContext.kind !== 'empty',
    isWholeDocumentSelected: normalizedContext.kind === 'document',
    selectedPages: normalizedContext.pages,
    selectedBlocks: normalizedContext.blocks,
    addWholeDocument,
    removePage,
    togglePage,
    toggleBlock,
    removeBlock,
    removeDeletedBlock,
    clearAll,
  }
}
