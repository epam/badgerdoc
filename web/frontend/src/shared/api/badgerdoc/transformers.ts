/**
 * BadgerDoc Data Transformers
 *
 * Transform BadgerDoc API responses to application types.
 * Handles coordinate conversion and data mapping.
 */

import type { Document } from '@/shared/types/api'
import type { BadgerDocExtractionPage, BadgerDocDocument, OverlayBox } from './types'

// =============================================================================
// Extended Hint Type with BadgerDoc-specific fields
// =============================================================================

export function transformHocrToHighlights(
  pages: BadgerDocExtractionPage[]
): Record<number, OverlayBox[]> {
  const overlays: Record<number, OverlayBox[]> = {}
  for (const page of pages) {
    const pageNumber = page.page_number
    if (!page.content) continue

    const pageRender = document.createElement('div')
    pageRender.innerHTML = page.content
    const pageOverlays: OverlayBox[] = []

    pageRender.querySelectorAll("[id^='block_']").forEach((element) => {
      const id = element.getAttribute('id') || ''
      const title = element.getAttribute('title') || ''
      const elementType = element.getAttribute('class') || ''
      const bboxMatch = title.match(/bbox (\d+) (\d+) (\d+) (\d+)/)

      if (bboxMatch && !['ocr_line', 'ocr_separator'].includes(elementType)) {
        const [, x1, y1, x2, y2] = bboxMatch.map(Number)
        pageOverlays.push({
          id,
          page: pageNumber,
          x: x1 / 1000,
          y: y1 / 1000,
          width: (x2 - x1) / 1000,
          height: (y2 - y1) / 1000,
        })
      }
    })
    overlays[pageNumber] = pageOverlays
  }

  return overlays
}

// =============================================================================
// Document Transformation
// =============================================================================

/**
 * Extract filename from Minio URL
 */
function extractFilenameFromUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname
    // Get the last segment of the path (filename)
    const segments = pathname.split('/')
    const filename = segments[segments.length - 1]
    // Remove query params that might be in the filename
    return filename.split('?')[0] || 'document.pdf'
  } catch {
    return 'document.pdf'
  }
}

/**
 * Transform BadgerDoc document to App Document type
 *
 * Note: BadgerDoc metadata is passed through as-is to support both article and patent types.
 * The overview tab handles type-specific rendering based on metadata.type field.
 */
export function transformBadgerDocDocument(
  bdDoc: BadgerDocDocument,
  defaults?: Partial<Document>
): Document {
  // Handle both 'file' and 'file_url' field names
  const pdfUrl = bdDoc.file || bdDoc.file_url || ''

  // Get title from metadata first, then fall back to filename
  const rawMetadata = bdDoc.metadata || {}
  const metadataTitle = rawMetadata.title as string | undefined
  const filename = bdDoc.name || extractFilenameFromUrl(pdfUrl)
  const title = metadataTitle || filename

  // Get document type from metadata
  const docType = (rawMetadata.type as string) || 'paper'

  // Get authors from metadata (handles both string and array)
  const rawAuthors = rawMetadata.authors || rawMetadata.author
  const authors: string[] = Array.isArray(rawAuthors)
    ? rawAuthors
    : typeof rawAuthors === 'string'
      ? rawAuthors
          .split(',')
          .map((a: string) => a.trim())
          .filter(Boolean)
      : []

  return {
    id: String(bdDoc.id),
    parentDocumentId: bdDoc.parent_document_id,
    title,
    extension: bdDoc.extension,
    type: docType as Document['type'],
    status: (bdDoc.status as Document['status']) || 'pending_review',
    pdfUrl,
    pageCount: 1, // Unknown from BadgerDoc
    metadata: rawMetadata,
    createdAt: bdDoc.created_at || new Date().toISOString(),
    updatedAt: bdDoc.updated_at || new Date().toISOString(),
    tags: bdDoc.tags || [],
    uploadedBy: bdDoc.uploaded_by,
    authors,
    abstract: (rawMetadata.abstract as string) || (rawMetadata.description as string) || '',
    publicationDate: (rawMetadata.publication_year as string) || bdDoc.created_at?.split('T')[0],
    ...defaults,
  }
}
