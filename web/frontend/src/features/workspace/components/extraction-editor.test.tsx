import { fireEvent, render, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ExtractionEditor from './extraction-editor'

const requestAnimationFrameMock = vi.fn<(callback: FrameRequestCallback) => number>((callback) => {
  callback(0)
  return 1
})

const cancelAnimationFrameMock = vi.fn()

const content = `
  <div class="ocr_carea" id="block_1_1" data-page="1" title="bbox 0 0 100 100">
    <p>First block</p>
  </div>
  <div class="ocr_carea" id="block_2_1" data-page="2" title="bbox 0 0 100 100">
    <p>Second block</p>
  </div>
`

describe('ExtractionEditor', () => {
  beforeEach(() => {
    vi.stubGlobal('requestAnimationFrame', requestAnimationFrameMock)
    vi.stubGlobal('cancelAnimationFrame', cancelAnimationFrameMock)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
    requestAnimationFrameMock.mockClear()
    cancelAnimationFrameMock.mockClear()
  })

  it('scrolls to an externally selected block after an editor selection of the already-active block', async () => {
    const scrollIntoViewSpy = vi.fn()
    const onBlockSelect = vi.fn()

    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      writable: true,
      value: scrollIntoViewSpy,
    })

    const { container, rerender } = render(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        activeBlockId="block_1_1"
        onBlockSelect={onBlockSelect}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
      expect(container.querySelector('[data-block-id="block_2_1"]')).not.toBeNull()
    })

    scrollIntoViewSpy.mockClear()

    const firstBlockHeader = container.querySelector(
      '[data-block-id="block_1_1"] [contenteditable="false"]'
    )
    expect(firstBlockHeader).not.toBeNull()

    fireEvent.click(firstBlockHeader!)

    expect(onBlockSelect).toHaveBeenCalledWith('block_1_1', 1)
    expect(scrollIntoViewSpy).not.toHaveBeenCalled()

    rerender(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        activeBlockId="block_2_1"
        onBlockSelect={onBlockSelect}
      />
    )

    await waitFor(() => {
      expect(scrollIntoViewSpy).toHaveBeenCalledTimes(1)
    })

    const secondBlock = container.querySelector('[data-block-id="block_2_1"]')
    expect(scrollIntoViewSpy).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' })
    expect(secondBlock).not.toBeNull()
  })

  it('resets the editor-originated selection guard after accepting changes', async () => {
    const scrollIntoViewSpy = vi.fn()
    const onBlockSelect = vi.fn()
    const onAcceptChanges = vi.fn().mockResolvedValue(undefined)

    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      writable: true,
      value: scrollIntoViewSpy,
    })

    const { container, rerender, getByRole } = render(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={true}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={onAcceptChanges}
        onBlockDelete={vi.fn()}
        activeBlockId="block_1_1"
        onBlockSelect={onBlockSelect}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    scrollIntoViewSpy.mockClear()

    const firstBlockHeader = container.querySelector(
      '[data-block-id="block_1_1"] [contenteditable="false"]'
    )
    expect(firstBlockHeader).not.toBeNull()

    fireEvent.click(firstBlockHeader!)
    expect(onBlockSelect).toHaveBeenCalledWith('block_1_1', 1)

    fireEvent.mouseDown(getByRole('button', { name: 'Accept' }))
    fireEvent.click(getByRole('button', { name: 'Accept' }))

    await waitFor(() => {
      expect(onAcceptChanges).toHaveBeenCalledTimes(1)
    })

    rerender(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={onAcceptChanges}
        onBlockDelete={vi.fn()}
        activeBlockId="block_2_1"
        onBlockSelect={onBlockSelect}
      />
    )

    await waitFor(() => {
      expect(scrollIntoViewSpy).toHaveBeenCalledTimes(1)
    })

    expect(scrollIntoViewSpy).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' })
  })
})
