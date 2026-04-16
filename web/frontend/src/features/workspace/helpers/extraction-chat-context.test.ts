import { describe, expect, it } from 'vitest'
import {
  EMPTY_EXTRACTION_CONTEXT,
  addBlockToContext,
  addDocumentToContext,
  addPageToContext,
  buildExtractionContextPayload,
  normalizeExtractionContext,
  removeBlockFromContext,
  toggleBlockInContext,
  togglePageInContext,
} from './extraction-chat-context'

describe('extraction chat context helpers', () => {
  it('lets whole document override every other selection', () => {
    const mixed = normalizeExtractionContext({
      kind: 'mixed',
      pages: [5, 2],
      blocks: [
        { blockId: 'block_5_1', pageNumber: 5 },
        { blockId: 'block_1_1', pageNumber: 1 },
      ],
    })

    expect(addDocumentToContext()).toEqual({
      kind: 'document',
      pages: [],
      blocks: [],
    })
    expect(normalizeExtractionContext({ ...mixed, kind: 'document' })).toEqual({
      kind: 'document',
      pages: [],
      blocks: [],
    })
  })

  it('removes page blocks when a page is selected', () => {
    const context = normalizeExtractionContext({
      kind: 'mixed',
      pages: [],
      blocks: [
        { blockId: 'block_2_1', pageNumber: 2 },
        { blockId: 'block_5_2', pageNumber: 5 },
      ],
    })

    expect(addPageToContext(context, 2)).toEqual({
      kind: 'mixed',
      pages: [2],
      blocks: [{ blockId: 'block_5_2', pageNumber: 5 }],
    })
  })

  it('does not add blocks that belong to already selected pages', () => {
    const context = normalizeExtractionContext({
      kind: 'mixed',
      pages: [2],
      blocks: [],
    })

    expect(addBlockToContext(context, { blockId: 'block_2_9', pageNumber: 2 })).toEqual(context)
  })

  it('supports mixed page and block selection across different pages', () => {
    const withPage = addPageToContext(EMPTY_EXTRACTION_CONTEXT, 2)
    const mixed = addBlockToContext(withPage, { blockId: 'block_5_3', pageNumber: 5 })

    expect(mixed).toEqual({
      kind: 'mixed',
      pages: [2],
      blocks: [{ blockId: 'block_5_3', pageNumber: 5 }],
    })
  })

  it('toggles pages and blocks cleanly', () => {
    const withPage = togglePageInContext(EMPTY_EXTRACTION_CONTEXT, 3)
    const withoutPage = togglePageInContext(withPage, 3)
    const withBlock = toggleBlockInContext(EMPTY_EXTRACTION_CONTEXT, {
      blockId: 'block_4_1',
      pageNumber: 4,
    })
    const withoutBlock = removeBlockFromContext(withBlock, 'block_4_1')

    expect(withPage.pages).toEqual([3])
    expect(withoutPage).toEqual(EMPTY_EXTRACTION_CONTEXT)
    expect(withBlock.blocks).toEqual([{ blockId: 'block_4_1', pageNumber: 4 }])
    expect(withoutBlock).toEqual(EMPTY_EXTRACTION_CONTEXT)
  })

  it('builds a normalized backend payload for mixed context', () => {
    const payload = buildExtractionContextPayload({
      context: normalizeExtractionContext({
        kind: 'mixed',
        pages: [5, 2],
        blocks: [
          { blockId: 'block_5_1', pageNumber: 5 },
          { blockId: 'block_4_3', pageNumber: 4 },
          { blockId: 'block_2_8', pageNumber: 2 },
        ],
      }),
      documentId: 11,
      extractionId: 22,
    })

    expect(payload).toEqual({
      kind: 'mixed',
      document_id: 11,
      extraction_id: 22,
      pages: [{ page_number: 2 }, { page_number: 5 }],
      blocks: [
        {
          blockId: 'block_4_3',
          pageNumber: 4,
          extraction_id: 22,
          xpath: '//*[@id="block_4_3"]',
          path: '/document/11/extraction/22/page/4/xpath//*[@id="block_4_3"]',
        },
      ],
    })
  })
})
