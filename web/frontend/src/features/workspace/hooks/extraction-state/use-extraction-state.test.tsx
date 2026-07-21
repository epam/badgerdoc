import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import { formatExtractionContentForEditor } from '@/features/workspace/helpers/extraction-utils'
import { useExtractionState } from './use-extraction-state'

const extractionPages: BadgerDocExtractionPage[] = [
  {
    page_number: 1,
    content: `<!DOCTYPE html><html><body>
      <div class="ocr_page" id="page_1" title="bbox 0 0 1000 1000">
        <div class="ocr_carea" id="block_1_1" title="bbox 0 0 100 100">
          <p>Original text</p>
        </div>
      </div>
    </body></html>`,
  },
]

const baselineHtml = formatExtractionContentForEditor(extractionPages)

const editedHtml = `
  <div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100">
    <p>Changed text</p>
  </div>
`

describe('useExtractionState', () => {
  it('builds a pending payload when the first extraction block is created', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages: [],
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    expect(result.current.hasChanges).toBe(true)
    expect(result.current.pendingPayload).toHaveLength(1)
    expect(result.current.pendingPayload[0].page).toBe(1)
    expect(result.current.pendingPayload[0].hocr).toContain(
      '<meta name="ocr-system" content="analysis"/>'
    )
    expect(result.current.pendingPayload[0].hocr).toContain('id="block_1_1"')
    expect(result.current.pendingPayload[0].hocr).toContain('bbox 100 200 400 600')
  })

  it('clears unsaved changes when edited text is restored to the original value', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.onBaselineReady(baselineHtml)
      result.current.onContentChange(editedHtml)
    })

    expect(result.current.hasChanges).toBe(true)

    act(() => {
      result.current.onContentChange(baselineHtml)
    })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toHaveLength(0)
  })

  it('clears unsaved changes when a newly created block is deleted', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.onBaselineReady(baselineHtml)
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    expect(result.current.hasChanges).toBe(true)

    const createdBlockId = result.current.createdBlockIds.values().next().value as string
    const baselineWithCreatedBlock = `
      <div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100">
        <p>Original text</p>
      </div>
      <div data-block-id="${createdBlockId}" data-page="1" data-block-title="bbox 100 200 400 600" data-new="true">
        <p>\u200B</p>
      </div>
    `

    act(() => {
      result.current.onBaselineReady(baselineWithCreatedBlock)
      result.current.onContentChange(baselineHtml)
      result.current.onBlockDelete(createdBlockId, 1)
    })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toHaveLength(0)
    expect(result.current.createdBlockIds.size).toBe(0)
    expect(result.current.deletedBlockIds).toHaveLength(0)
  })

  it('keeps text pending changes when a created block is deleted on an edited page', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.onBaselineReady(baselineHtml)
      result.current.onContentChange(editedHtml)
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    const createdBlockId = result.current.createdBlockIds.values().next().value as string
    const editedWithCreatedBlock = `
      <div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100">
        <p>Changed text</p>
      </div>
      <div data-block-id="${createdBlockId}" data-page="1" data-block-title="bbox 100 200 400 600" data-new="true">
        <p>\u200B</p>
      </div>
    `

    act(() => {
      result.current.onBaselineReady(editedWithCreatedBlock)
      result.current.onContentChange(editedHtml)
      result.current.onBlockDelete(createdBlockId, 1)
    })

    expect(result.current.hasChanges).toBe(true)
    expect(result.current.pendingPayload).toHaveLength(1)
    expect(result.current.pendingPayload[0].hocr).toContain('Changed text')
  })

  it('clears unsaved changes after edit, create, delete, then manual text revert', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.onBaselineReady(baselineHtml)
      result.current.onContentChange(editedHtml)
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    const createdBlockId = result.current.createdBlockIds.values().next().value as string
    const editedWithCreatedBlock = `
      <div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100">
        <p>Changed text</p>
      </div>
      <div data-block-id="${createdBlockId}" data-page="1" data-block-title="bbox 100 200 400 600" data-new="true">
        <p>\u200B</p>
      </div>
    `

    act(() => {
      result.current.onBaselineReady(editedWithCreatedBlock)
      result.current.onContentChange(editedHtml)
      result.current.onBlockDelete(createdBlockId, 1)
    })

    expect(result.current.hasChanges).toBe(true)

    act(() => {
      result.current.onContentChange(baselineHtml)
    })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toHaveLength(0)
  })

  it('clears unsaved changes after edit, create, delete, then tiptap-style manual revert', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.onBaselineReady(baselineHtml)
      result.current.onContentChange(editedHtml)
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    const createdBlockId = result.current.createdBlockIds.values().next().value as string
    const editedWithCreatedBlock = `
      <div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100">
        <p>Changed text</p>
      </div>
      <div data-block-id="${createdBlockId}" data-page="1" data-block-title="bbox 100 200 400 600" data-new="true">
        <p>\u200B</p>
      </div>
    `
    const tiptapOriginalHtml =
      '<div data-block-id="block_1_1" data-page="1" data-block-title="bbox 0 0 100 100"><p>Original text</p></div>'

    act(() => {
      result.current.onBaselineReady(editedWithCreatedBlock)
      result.current.onContentChange(editedHtml)
      result.current.onBlockDelete(createdBlockId, 1)
    })

    expect(result.current.hasChanges).toBe(true)

    act(() => {
      result.current.onBaselineReady(editedHtml)
      result.current.onContentChange(tiptapOriginalHtml)
    })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toHaveLength(0)
  })
})
