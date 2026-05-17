/**
 * Hook for fetching extraction pages from BadgerDoc API
 *
 * Fetches extraction page data filtered by tags (e.g., 'extraction', 'analysis').
 * Returns blocks containing paragraphs, tables, and other extracted content.
 *
 * Supports fetching by:
 * - Document ID + tags (default, uses latest extraction)
 * - Extraction ID (specific version, used by dev menu)
 */

import { useQuery } from '@tanstack/react-query'
import { getApiAdapter } from '../adapters/factory'

/**
 * Query keys for extraction pages
 */
export const extractionPagesKeys = {
  all: ['badgerdoc-extraction-pages'] as const,
  document: (documentId: string) => [...extractionPagesKeys.all, documentId] as const,
  documentWithTags: (documentId: string, tags?: string) =>
    [...extractionPagesKeys.document(documentId), tags] as const,
}

/**
 * Fetch extraction pages for a document from BadgerDoc API
 *
 * @param documentId - The document ID to fetch extraction pages for
 * @param tags - Optional tag filter (e.g., 'extraction', 'analysis')
 * @returns React Query result with extraction pages data
 */
export function useBadgerDocExtractionPages(documentId: string, tags?: string, enabled = true) {
  return useQuery({
    queryKey: extractionPagesKeys.documentWithTags(documentId, tags),
    queryFn: () => {
      return getApiAdapter().extractions.getLatestExtraction(documentId, tags)
    },
    enabled: !!documentId && enabled,
    staleTime: 30_000, // Consider data stale after 30 seconds
    refetchOnWindowFocus: false,
  })
}
