import { fireEvent, render, waitFor, within } from '@testing-library/react'
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

const contentWithConflictBlock = `
  <div class="ocr_carea" id="block_1_1" data-page="1" title="bbox 0 0 100 100">
    <p>First block</p>
  </div>
  <div class="ocr_carea conflict" id="block_1_2" data-page="1" title="bbox 0 100 100 200">
    <p>Conflicting block</p>
  </div>
`

const contentWithConflictTabs = `
  <div class="ocr_carea conflict conflict-group--block_1_4 conflict-variant--council" id="block_1_4" data-page="1" title="bbox 0 100 300 220">
    <p class="ocr_par"><span class="ocr_line">Recorded By/Date:</span></p>
    <p class="ocr_par"><span class="ocr_line"><span class="conflict-target">13NOV23</span></span></p>
    <p class="ocr_par conflict-comment"><span class="ocr_line">Consensus reached on 13NOV23.</span></p>
  </div>
  <div class="ocr_carea conflict conflict-group--block_1_4 conflict-variant--miner-u" id="block_1_4__miner_u" data-page="1" title="bbox 0 100 300 220">
    <p class="ocr_par"><span class="ocr_line">Recorded By/Date:</span></p>
    <p class="ocr_par"><span class="ocr_line"><span class="conflict-target">13N0V23</span></span></p>
    <p class="ocr_par conflict-comment"><span class="ocr_line">Miner-U suggested 13N0V23.</span></p>
  </div>
  <div class="ocr_carea conflict conflict-group--block_1_4 conflict-variant--gpt-4-vision" id="block_1_4__gpt_4_vision" data-page="1" title="bbox 0 100 300 220">
    <p class="ocr_par"><span class="ocr_line">Recorded By/Date:</span></p>
    <p class="ocr_par"><span class="ocr_line"><span class="conflict-target">13NOV23</span></span></p>
    <p class="ocr_par conflict-comment"><span class="ocr_line">GPT-4 Vision confirmed 13NOV23.</span></p>
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
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
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
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
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
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
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
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
        activeBlockId="block_2_1"
        onBlockSelect={onBlockSelect}
      />
    )

    await waitFor(() => {
      expect(scrollIntoViewSpy).toHaveBeenCalledTimes(1)
    })

    expect(scrollIntoViewSpy).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' })
  })

  it('disables block context actions when prompt context becomes unavailable', async () => {
    const onToggleBlockContext = vi.fn()

    const { container, rerender } = render(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={onToggleBlockContext}
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    const firstBlock = container.querySelector('[data-block-id="block_1_1"]')
    expect(firstBlock).not.toBeNull()

    let contextButton = within(firstBlock as HTMLElement).getByRole('button', {
      name: /add block to context/i,
    })

    expect(contextButton).toBeEnabled()

    rerender(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={onToggleBlockContext}
        isContextInteractionDisabled
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(
        within(firstBlock as HTMLElement).getByRole('button', {
          name: /prompt context is unavailable while you have unsaved changes\./i,
        })
      ).toBeDisabled()
    })

    contextButton = within(firstBlock as HTMLElement).getByRole('button', {
      name: /prompt context is unavailable while you have unsaved changes\./i,
    })

    expect(contextButton).toBeDisabled()

    fireEvent.click(contextButton)
    expect(onToggleBlockContext).not.toHaveBeenCalled()
  })

  it('highlights extraction blocks marked with the conflict hOCR class', async () => {
    const { container } = render(
      <ExtractionEditor
        content={contentWithConflictBlock}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_2"]')).not.toBeNull()
    })

    const conflictBlock = container.querySelector('[data-block-id="block_1_2"]')

    expect(conflictBlock).toHaveClass('ocr_carea')
    expect(conflictBlock).toHaveClass('conflict')
    expect(conflictBlock).toHaveClass('border-l-amber-500')
    expect(conflictBlock).toHaveClass('bg-amber-50/70')
  })

  it('renders conflict variants as tabs and switches the visible variant', async () => {
    const { container, getByRole } = render(
      <ExtractionEditor
        content={contentWithConflictTabs}
        hasUnsavedChanges={false}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={vi.fn()}
        onAcceptChanges={vi.fn().mockResolvedValue(undefined)}
        onBlockDelete={vi.fn()}
        selectedContextBlockIds={[]}
        selectedContextPages={[]}
        isWholeDocumentSelected={false}
        onToggleBlockContext={vi.fn()}
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_4"]')).not.toBeNull()
      expect(container.querySelector('[data-block-id="block_1_4__miner_u"]')).not.toBeNull()
    })

    const councilBlock = container.querySelector('[data-block-id="block_1_4"]') as HTMLElement
    const minerBlock = container.querySelector(
      '[data-block-id="block_1_4__miner_u"]'
    ) as HTMLElement

    expect(councilBlock).toBeVisible()
    expect(minerBlock).not.toBeVisible()
    expect(within(councilBlock).getByText('Consensus reached on 13NOV23.')).toBeInTheDocument()
    expect(councilBlock.querySelector('.conflict-target')).not.toBeNull()

    fireEvent.click(getByRole('button', { name: 'miner u' }))

    await waitFor(() => {
      expect(minerBlock).toBeVisible()
    })

    expect(councilBlock).not.toBeVisible()
    expect(within(minerBlock).getByText('Miner-U suggested 13N0V23.')).toBeInTheDocument()
    expect(within(minerBlock).getByText('13N0V23')).toBeInTheDocument()
  })
})
