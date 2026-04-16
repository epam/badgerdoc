export interface ExtractionContextBlock {
  blockId: string
  pageNumber: number
}

export interface NormalizedExtractionContext {
  kind: 'empty' | 'document' | 'mixed'
  pages: number[]
  blocks: ExtractionContextBlock[]
}

export interface ExtractionContextPayloadBlock extends ExtractionContextBlock {
  extraction_id: number | null
  xpath: string
  path: string
}

export interface ExtractionContextPayload {
  kind: 'document' | 'mixed'
  document_id: number
  extraction_id: number | null
  pages: Array<{ page_number: number }>
  blocks: ExtractionContextPayloadBlock[]
}

export const EMPTY_EXTRACTION_CONTEXT: NormalizedExtractionContext = {
  kind: 'empty',
  pages: [],
  blocks: [],
}

function uniqueSortedPages(pages: number[]) {
  return [...new Set(pages)].sort((a, b) => a - b)
}

function uniqueBlocks(blocks: ExtractionContextBlock[]) {
  const next = new Map<string, ExtractionContextBlock>()

  blocks.forEach((block) => {
    next.set(block.blockId, block)
  })

  return [...next.values()].sort((left, right) => {
    if (left.pageNumber !== right.pageNumber) {
      return left.pageNumber - right.pageNumber
    }

    return left.blockId.localeCompare(right.blockId)
  })
}

export function normalizeExtractionContext(
  context: Partial<NormalizedExtractionContext> | null | undefined
): NormalizedExtractionContext {
  if (!context || context.kind === 'empty') {
    return EMPTY_EXTRACTION_CONTEXT
  }

  if (context.kind === 'document') {
    return {
      kind: 'document',
      pages: [],
      blocks: [],
    }
  }

  const pages = uniqueSortedPages(context.pages ?? [])
  const pageSet = new Set(pages)
  const blocks = uniqueBlocks(
    (context.blocks ?? []).filter((block) => !pageSet.has(block.pageNumber))
  )

  if (pages.length === 0 && blocks.length === 0) {
    return EMPTY_EXTRACTION_CONTEXT
  }

  return {
    kind: 'mixed',
    pages,
    blocks,
  }
}

export function addDocumentToContext(): NormalizedExtractionContext {
  return {
    kind: 'document',
    pages: [],
    blocks: [],
  }
}

export function clearExtractionContext(): NormalizedExtractionContext {
  return EMPTY_EXTRACTION_CONTEXT
}

export function addPageToContext(
  context: NormalizedExtractionContext,
  pageNumber: number
): NormalizedExtractionContext {
  if (context.kind === 'document') {
    return context
  }

  return normalizeExtractionContext({
    kind: 'mixed',
    pages: [...context.pages, pageNumber],
    blocks: context.blocks.filter((block) => block.pageNumber !== pageNumber),
  })
}

export function removePageFromContext(
  context: NormalizedExtractionContext,
  pageNumber: number
): NormalizedExtractionContext {
  if (context.kind === 'document') {
    return context
  }

  return normalizeExtractionContext({
    kind: 'mixed',
    pages: context.pages.filter((page) => page !== pageNumber),
    blocks: context.blocks,
  })
}

export function togglePageInContext(
  context: NormalizedExtractionContext,
  pageNumber: number
): NormalizedExtractionContext {
  if (context.pages.includes(pageNumber)) {
    return removePageFromContext(context, pageNumber)
  }

  return addPageToContext(context, pageNumber)
}

export function addBlockToContext(
  context: NormalizedExtractionContext,
  block: ExtractionContextBlock
): NormalizedExtractionContext {
  if (context.kind === 'document' || context.pages.includes(block.pageNumber)) {
    return context
  }

  return normalizeExtractionContext({
    kind: 'mixed',
    pages: context.pages,
    blocks: [...context.blocks, block],
  })
}

export function removeBlockFromContext(
  context: NormalizedExtractionContext,
  blockId: string
): NormalizedExtractionContext {
  if (context.kind === 'document') {
    return context
  }

  return normalizeExtractionContext({
    kind: 'mixed',
    pages: context.pages,
    blocks: context.blocks.filter((block) => block.blockId !== blockId),
  })
}

export function toggleBlockInContext(
  context: NormalizedExtractionContext,
  block: ExtractionContextBlock
): NormalizedExtractionContext {
  if (context.blocks.some((item) => item.blockId === block.blockId)) {
    return removeBlockFromContext(context, block.blockId)
  }

  return addBlockToContext(context, block)
}

export function removeDeletedBlockFromContext(
  context: NormalizedExtractionContext,
  blockId: string
): NormalizedExtractionContext {
  return removeBlockFromContext(context, blockId)
}

export function buildExtractionContextPayload({
  context,
  documentId,
  extractionId,
}: {
  context: NormalizedExtractionContext
  documentId: number
  extractionId: number | null
}): ExtractionContextPayload | null {
  const normalized = normalizeExtractionContext(context)

  if (normalized.kind === 'empty') {
    return null
  }

  if (normalized.kind === 'document') {
    return {
      kind: 'document',
      document_id: documentId,
      extraction_id: extractionId,
      pages: [],
      blocks: [],
    }
  }

  return {
    kind: 'mixed',
    document_id: documentId,
    extraction_id: extractionId,
    pages: normalized.pages.map((pageNumber) => ({ page_number: pageNumber })),
    blocks: normalized.blocks.map((block) => ({
      ...block,
      extraction_id: extractionId,
      xpath: `//*[@id="${block.blockId}"]`,
      path: `/document/${documentId}/extraction/${extractionId ?? 'unknown'}/page/${block.pageNumber}/xpath//*[@id="${block.blockId}"]`,
    })),
  }
}

export function getContextBlockLabel(blockId: string) {
  const match = blockId.match(/^block_(\d+)_(.+)$/)
  if (!match) {
    return `Block ${blockId}`
  }

  return `Block ${match[1]}.${match[2]}`
}
