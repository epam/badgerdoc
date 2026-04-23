import { useCallback, useMemo, useState } from 'react'
import type { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  appendPromptContextLink,
  buildBlockContextPath,
  buildDocumentContextPath,
  buildPageContextPath,
  removePromptContextLinks,
  summarizePromptContext,
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
  const promptKey = `${documentId}:${extractionId ?? 'none'}:${activeTag ?? 'overview'}`
  const [promptState, setPromptState] = useState({
    key: promptKey,
    prompt: '',
  })

  if (promptState.key !== promptKey) {
    setPromptState({
      key: promptKey,
      prompt: '',
    })
  }

  const setPrompt = useCallback((prompt: string) => {
    setPromptState((prev) => ({ ...prev, prompt }))
  }, [])

  const appendContextPath = useCallback((path: string) => {
    setPromptState((prev) => ({
      ...prev,
      prompt: appendPromptContextLink(prev.prompt, path),
    }))
  }, [])

  const addWholeDocument = useCallback(() => {
    appendContextPath(buildDocumentContextPath(documentId))
  }, [appendContextPath, documentId])

  const addPage = useCallback(
    (pageNumber: number) => {
      appendContextPath(buildPageContextPath({ documentId, extractionId, pageNumber }))
    },
    [appendContextPath, documentId, extractionId]
  )

  const toggleBlock = useCallback(
    (block: ExtractionContextBlock) => {
      const path = buildBlockContextPath({
        documentId,
        extractionId,
        pageNumber: block.pageNumber,
        blockId: block.blockId,
      })

      if (!path) return

      appendContextPath(path)
    },
    [appendContextPath, documentId, extractionId]
  )

  const removeBlock = useCallback((blockId: string) => {
    setPromptState((prev) => ({
      ...prev,
      prompt: removePromptContextLinks(prev.prompt, (token) => token.blockId === blockId),
    }))
  }, [])

  const prompt = promptState.prompt
  const summary = useMemo(() => summarizePromptContext(prompt), [prompt])

  return {
    prompt,
    extractionId,
    hasContext: summary.hasContext,
    isWholeDocumentSelected: summary.isWholeDocumentSelected,
    selectedPages: summary.selectedPages,
    selectedBlocks: summary.selectedBlocks,
    addWholeDocument,
    togglePage: addPage,
    toggleBlock,
    removeBlock,
    setPrompt,
  }
}
