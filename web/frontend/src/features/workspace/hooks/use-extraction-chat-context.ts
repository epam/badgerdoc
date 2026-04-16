import { useCallback, useEffect, useMemo, useState } from 'react'
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
  const [context, setContext] = useState(EMPTY_EXTRACTION_CONTEXT)

  const extractionId = extractionPages?.[0]?.extraction_id ?? null

  useEffect(() => {
    setContext(EMPTY_EXTRACTION_CONTEXT)
  }, [documentId, extractionId, activeTag])

  const addWholeDocument = useCallback(() => {
    setContext(addDocumentToContext())
  }, [])

  const removePage = useCallback((pageNumber: number) => {
    setContext((prev) => removePageFromContext(prev, pageNumber))
  }, [])

  const togglePage = useCallback((pageNumber: number) => {
    setContext((prev) => togglePageInContext(prev, pageNumber))
  }, [])

  const toggleBlock = useCallback((block: ExtractionContextBlock) => {
    setContext((prev) => toggleBlockInContext(prev, block))
  }, [])

  const removeBlock = useCallback((blockId: string) => {
    setContext((prev) => removeBlockFromContext(prev, blockId))
  }, [])

  const clearAll = useCallback(() => {
    setContext(clearExtractionContext())
  }, [])

  const removeDeletedBlock = useCallback((blockId: string) => {
    setContext((prev) => removeDeletedBlockFromContext(prev, blockId))
  }, [])

  const normalizedContext = useMemo(() => normalizeExtractionContext(context), [context])
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
