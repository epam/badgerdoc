import { useCallback, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getApiAdapter } from '@/shared/api/adapters/factory'
import { BadgerDocExtraction } from '@/shared/api/badgerdoc/types'
import { extractionPagesKeys } from '@/shared/api/hooks'

interface UseExtractionApiParams {
  documentId: string
  activeTag?: string
}

export const USER_INPUT_EXTRACTION_TAG = 'user-input'
const DEFAULT_EXTRACTION_TAG = 'deepseek-ocr-2'

export function withUserInputTag(tags: Array<string | undefined | null>) {
  const uniqueTags = new Set(tags.filter((tag): tag is string => Boolean(tag)))
  uniqueTags.add(USER_INPUT_EXTRACTION_TAG)
  return Array.from(uniqueTags)
}

export function useExtractionApi({ documentId, activeTag }: UseExtractionApiParams) {
  const apiAdapter = getApiAdapter()
  const queryClient = useQueryClient()
  const extractionInProgressRef = useRef<BadgerDocExtraction | null>(null)
  const [isPending, setIsPending] = useState(false)

  const ensureExtraction = useCallback(async () => {
    if (!extractionInProgressRef.current) {
      const tags = withUserInputTag([activeTag ?? DEFAULT_EXTRACTION_TAG])
      const extraction = await apiAdapter.extractions.createExtraction({
        documentId,
        status: 'Started',
        tags,
      })
      extractionInProgressRef.current = {
        ...extraction,
        tags: withUserInputTag(extraction.tags?.length ? extraction.tags : tags),
      }
    }

    return extractionInProgressRef.current
  }, [apiAdapter.extractions, activeTag, documentId])

  const saveExtractionPages = useCallback(
    async (payload: Array<{ page: number; hocr: string }>) => {
      if (!payload.length) {
        return null
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

        return extraction
      } finally {
        setIsPending(false)
      }
    },
    [apiAdapter.extractions, ensureExtraction]
  )

  const acceptExtraction = useCallback(
    async (payload: Array<{ page: number; hocr: string }>) => {
      if (!payload.length) {
        return null
      }

      setIsPending(true)

      try {
        const savedExtraction = await saveExtractionPages(payload)

        const extraction = savedExtraction ?? (await ensureExtraction())
        const completedExtraction = await apiAdapter.extractions.updateExtraction({
          extractionId: extraction.id,
          status: 'Completed',
          tags: withUserInputTag(extraction.tags),
        })
        extractionInProgressRef.current = null

        // Refetch extraction pages so the query cache reflects saved data
        // before acceptChanges() clears editedExtractionPages
        await queryClient.invalidateQueries({
          queryKey: extractionPagesKeys.documentWithTags(documentId, activeTag),
        })

        return completedExtraction
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
