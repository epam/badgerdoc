import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  appendPromptContextLink,
  buildBlockContextPath,
  buildDocumentContextPath,
  buildPageContextPath,
  type PromptContextPathInserter,
  removePromptContextLinks,
  summarizePromptContext,
  type ExtractionContextBlock,
} from '@/features/workspace/helpers/extraction-chat-context'

interface UseExtractionChatContextParams {
  documentId: string
  extractionPages?: BadgerDocExtractionPage[]
}

export const PROMPT_DRAFT_STORAGE_KEY = 'badgerdoc.prompt'
export const PROMPT_DRAFT_STORAGE_DEBOUNCE_MS = 400

function readStoredPromptDraft() {
  if (typeof window === 'undefined') {
    return ''
  }

  try {
    const storedPrompt = window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)
    return typeof storedPrompt === 'string' ? storedPrompt : ''
  } catch {
    return ''
  }
}

function writeStoredPromptDraft(prompt: string) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(PROMPT_DRAFT_STORAGE_KEY, prompt)
  } catch {
    // Keep the editor usable even when localStorage is unavailable.
  }
}

export function useExtractionChatContext({
  documentId,
  extractionPages,
}: UseExtractionChatContextParams) {
  const extractionId = extractionPages?.[0]?.extraction_id ?? null
  const [prompt, setPrompt] = useState(readStoredPromptDraft)
  const promptRef = useRef(prompt)
  promptRef.current = prompt
  const promptContextInserterRef = useRef<PromptContextPathInserter | null>(null)

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      writeStoredPromptDraft(prompt)
    }, PROMPT_DRAFT_STORAGE_DEBOUNCE_MS)

    return () => window.clearTimeout(timeoutId)
  }, [prompt])

  useEffect(() => {
    return () => writeStoredPromptDraft(promptRef.current)
  }, [])

  const registerPromptContextInserter = useCallback(
    (inserter: PromptContextPathInserter | null) => {
      promptContextInserterRef.current = inserter
    },
    []
  )

  const appendContextPath = useCallback((path: string) => {
    if (promptContextInserterRef.current) {
      promptContextInserterRef.current(path)
      return
    }

    setPrompt((prev) => appendPromptContextLink(prev, path))
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

  const removeBlocks = useCallback((blockIds: string[]) => {
    if (!blockIds.length) return

    const blockIdsSet = new Set(blockIds)

    setPrompt((prev) =>
      removePromptContextLinks(prev, (token) =>
        token.blockId ? blockIdsSet.has(token.blockId) : false
      )
    )
  }, [])

  const summary = useMemo(() => summarizePromptContext(prompt), [prompt])

  return {
    prompt,
    extractionId,
    hasContext: summary.hasContext,
    isWholeDocumentSelected: summary.isWholeDocumentSelected,
    selectedPages: summary.selectedPages,
    selectedBlocks: summary.selectedBlocks,
    registerPromptContextInserter,
    addWholeDocument,
    togglePage: addPage,
    toggleBlock,
    removeBlocks,
    setPrompt,
  }
}
