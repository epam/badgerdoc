import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useExtractionState } from './use-extraction-state'
import type { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'

const extractionPages: BadgerDocExtractionPage[] = [
  {
    page_number: 1,
    content: `
      <div class="ocr_page" id="page_1" title="bbox 0 0 1000 1000">
        <div class="ocr_carea" id="block_1_1" title="bbox 10 10 100 40">
          <p>First block</p>
        </div>
        <div class="ocr_carea" id="block_1_2" title="bbox 10 50 100 80">
          <p>Second block</p>
        </div>
      </div>
    `,
  },
]

const editorHtml = `
  <div data-block-id="block_1_1" data-block-title="bbox 10 10 100 40" data-page="1">
    <p>First block</p>
  </div>
  <div data-block-id="block_1_2" data-block-title="bbox 10 50 100 80" data-page="1">
    <p>Second block</p>
  </div>
`

describe('useExtractionState', () => {
  it('tracks edited content as pending payload', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'deepseek-ocr-2',
      })
    )

    const updatedHtml = editorHtml.replace('First block', 'First block updated')

    act(() => {
      result.current.onBaselineReady(editorHtml)
      result.current.onContentChange(updatedHtml)
    })

    expect(result.current.hasChanges).toBe(true)
    expect(result.current.pendingPayload).toHaveLength(1)
    expect(result.current.pendingPayload[0].page).toBe(1)
    expect(result.current.pendingPayload[0].hocr).toContain('First block updated')
  })

  it('accepts pending changes and clears dirty state', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages,
        activeTag: 'deepseek-ocr-2',
      })
    )

    const updatedHtml = editorHtml.replace('First block', 'First block updated')

    act(() => {
      result.current.onBaselineReady(editorHtml)
      result.current.onContentChange(updatedHtml)
    })

    expect(result.current.hasChanges).toBe(true)

    act(() => {
      result.current.acceptChanges()
    })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toEqual([])
    expect(result.current.scopedExtractionPages?.[0].content).toContain('First block updated')
  })

  it('resets edit state when the active tag changes', () => {
    const { result, rerender } = renderHook(
      ({ activeTag }: { activeTag: string }) =>
        useExtractionState({
          extractionPages,
          activeTag,
        }),
      {
        initialProps: { activeTag: 'deepseek-ocr-2' },
      }
    )

    const updatedHtml = editorHtml.replace('First block', 'First block updated')

    act(() => {
      result.current.setActiveBlockId('block_1_1')
      result.current.onBaselineReady(editorHtml)
      result.current.onContentChange(updatedHtml)
    })

    expect(result.current.hasChanges).toBe(true)
    expect(result.current.activeBlockId).toBe('block_1_1')

    rerender({ activeTag: 'analysis' })

    expect(result.current.hasChanges).toBe(false)
    expect(result.current.pendingPayload).toEqual([])
    expect(result.current.activeBlockId).toBeNull()
  })
})
