import { useCallback, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getApiAdapter } from '@/shared/api/adapters/factory'
import { BadgerDocExtraction } from '@/shared/api/badgerdoc/types'
import { extractionPagesKeys } from '@/shared/api/hooks'

interface UseExtractionApiParams {
  documentId: string
  activeTag?: string
}

export function useExtractionApi({ documentId, activeTag }: UseExtractionApiParams) {
  const apiAdapter = getApiAdapter()
  const queryClient = useQueryClient()
  const extractionInProgressRef = useRef<BadgerDocExtraction | null>(null)
  const [isPending, setIsPending] = useState(false)

  const ensureExtraction = useCallback(async () => {
    if (!extractionInProgressRef.current) {
      const extraction = await apiAdapter.extractions.createExtraction({
        documentId,
        status: 'Started',
        tags: [activeTag ?? 'deepseek-ocr-2'],
      })
      extractionInProgressRef.current = extraction
    }

    return extractionInProgressRef.current
  }, [apiAdapter.extractions, activeTag, documentId])

  const saveExtractionPages = useCallback(
    async (payload: Array<{ page: number; hocr: string }>) => {
      if (!payload.length) {
        return
      }

      setIsPending(true)

      try {
        const extraction = await ensureExtraction()

        for (const { page, hocr } of payload) {
          try {
            await apiAdapter.extractions.updateExtractionPage({
              extractionId: extraction.id,
              pageNumber: page,
              content: hocr,
            })
          } catch {
            await apiAdapter.extractions.createExtractionPage({
              extractionId: extraction.id,
              pageNumber: page,
              content: hocr,
            })
          }
        }
      } finally {
        setIsPending(false)
      }
    },
    [apiAdapter.extractions, ensureExtraction]
  )

  const acceptExtraction = useCallback(
    async (payload: Array<{ page: number; hocr: string }>) => {
      if (!payload.length) {
        return
      }

      setIsPending(true)

      try {
        await saveExtractionPages(payload)

        const extraction = await ensureExtraction()
        await apiAdapter.extractions.updateExtraction({
          extractionId: extraction.id,
          status: 'Completed',
        })
        extractionInProgressRef.current = null

        // Refetch extraction pages so the query cache reflects saved data
        // before acceptChanges() clears editedExtractionPages
        await queryClient.invalidateQueries({
          queryKey: extractionPagesKeys.documentWithTags(documentId, activeTag),
        })
      } finally {
        setIsPending(false)
      }
    },
    [
      apiAdapter.extractions,
      documentId,
      activeTag,
      ensureExtraction,
      queryClient,
      saveExtractionPages,
    ]
  )

  return {
    saveExtractionPages,
    acceptExtraction,
    isPending,
  }
}
