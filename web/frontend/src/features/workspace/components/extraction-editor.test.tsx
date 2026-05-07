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

const existingBlock = `
  <div class="ocr_carea" id="block_1_1" data-page="1" title="bbox 0 0 100 100">
    <p>First block</p>
  </div>
`

const userCreatedBlock = `
  <div class="ocr_carea" id="block_1_2" data-page="1" data-new="true" title="bbox 10 10 50 50">
    <p>\u200B</p>
  </div>
`

const hocrBlock = `
  <div class="ocr_carea" id="block_1_1" data-page="1" title="bbox 187 9 712 21">
    <p class="ocr_par" id="par_1_1" lang="eng" title="bbox 187 9 712 21">
      <span class="ocr_textfloat" id="line_1_1" title="bbox 187 9 712 21">
        <span class="ocrx_word" id="word_1_1" title="bbox 187 9 289 18">REP-0337001</span>
        <span class="ocrx_word" id="word_1_2" title="bbox 296 9 329 18">v1.0</span>
        <span class="ocrx_word" id="word_1_3" title="bbox 347 9 396 18">Status:</span>
        <span class="ocrx_word" id="word_1_4" title="bbox 402 9 476 21">Approved</span>
      </span>
    </p>
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

  it('parses OCR words inline on initial mount', async () => {
    const { container } = render(
      <ExtractionEditor
        content={hocrBlock}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    const blockContent = container.querySelector(
      '[data-block-id="block_1_1"] [data-node-view-content]'
    )
    expect(blockContent!.querySelectorAll('p').length).toBe(1)
    expect(blockContent!.textContent).toContain('REP-0337001 v1.0 Status: Approved')
  })

  it('does not reset content when hasUnsavedChanges flips without a content prop change', async () => {
    const { container, rerender } = render(
      <ExtractionEditor
        content={existingBlock}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    rerender(
      <ExtractionEditor
        content={existingBlock}
        hasUnsavedChanges={true}
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

    const blockContent = container.querySelector(
      '[data-block-id="block_1_1"] [data-node-view-content]'
    )
    expect(blockContent?.textContent).toContain('First block')
  })

  it('keeps OCR words inline when new blocks arrive without unsaved changes', async () => {
    // Simulates OCR workflow completion: editor already mounted, no pending edits.
    const { container, rerender } = render(
      <ExtractionEditor
        content=""
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

    rerender(
      <ExtractionEditor
        content={hocrBlock}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    const blockContent = container.querySelector(
      '[data-block-id="block_1_1"] [data-node-view-content]'
    )
    expect(blockContent).not.toBeNull()
    expect(blockContent!.querySelectorAll('p').length).toBe(1)
    expect(blockContent!.textContent).toContain('REP-0337001 v1.0 Status: Approved')
  })

  it('keeps OCR words inline when OCR blocks arrive while unsaved changes exist', async () => {
    // Simulates OCR finishing while the user was editing: must not use insertContentAt.
    const { container, rerender } = render(
      <ExtractionEditor
        content={existingBlock}
        hasUnsavedChanges={true}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    rerender(
      <ExtractionEditor
        content={`${existingBlock}${hocrBlock.replace('block_1_1', 'block_1_2')}`}
        hasUnsavedChanges={true}
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

    const ocrBlockContent = container.querySelector(
      '[data-block-id="block_1_2"] [data-node-view-content]'
    )
    expect(ocrBlockContent).not.toBeNull()
    expect(ocrBlockContent!.querySelectorAll('p').length).toBe(1)
    expect(ocrBlockContent!.textContent).toContain('REP-0337001 v1.0 Status: Approved')
  })

  it('incrementally inserts only user-created blocks while preserving existing blocks', async () => {
    // Simulates drawing a new region on the PDF while text edits are pending.
    const onBaselineReady = vi.fn()

    const { container, rerender } = render(
      <ExtractionEditor
        content={existingBlock}
        hasUnsavedChanges={true}
        onBaselineReady={onBaselineReady}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    onBaselineReady.mockClear()

    rerender(
      <ExtractionEditor
        content={`${existingBlock}${userCreatedBlock}`}
        hasUnsavedChanges={true}
        onBaselineReady={onBaselineReady}
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

    expect(container.querySelectorAll('[data-block-id]').length).toBe(2)
    expect(
      container.querySelector('[data-block-id="block_1_1"] [data-node-view-content]')!.textContent
    ).toContain('First block')
    expect(
      container.querySelector('[data-block-id="block_1_2"] [data-node-view-content]')
    ).not.toBeNull()
    expect(onBaselineReady).toHaveBeenCalled()
  })

  it('replaces content when existing blocks are removed from incoming data', async () => {
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
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_2_1"]')).not.toBeNull()
    })

    rerender(
      <ExtractionEditor
        content={existingBlock}
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
      expect(container.querySelector('[data-block-id="block_2_1"]')).toBeNull()
    })

    expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
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

  it('does not auto-accept changes when the editor unmounts during a revert', async () => {
    const onAcceptChanges = vi.fn().mockResolvedValue(undefined)
    const onRevertChanges = vi.fn()

    const { container, getByRole, unmount } = render(
      <ExtractionEditor
        content={content}
        hasUnsavedChanges={true}
        onBaselineReady={vi.fn()}
        onContentChange={vi.fn()}
        onRevertChanges={onRevertChanges}
        onAcceptChanges={onAcceptChanges}
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
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

    fireEvent.mouseDown(getByRole('button', { name: 'Revert' }))
    fireEvent.click(getByRole('button', { name: 'Revert' }))

    expect(onRevertChanges).toHaveBeenCalledTimes(1)

    // Reverting on a tab that becomes empty unmounts the editor (onDestroy).
    // The revert guard must keep onDestroy from re-persisting the discarded block.
    unmount()

    // onDestroy runs handleAcceptChanges asynchronously, so flush microtasks
    // before asserting it was suppressed (a negative waitFor would pass at t=0).
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(onAcceptChanges).not.toHaveBeenCalled()
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

  it('uses the latest block context callback after rerendering an existing editor', async () => {
    const oldToggleBlockContext = vi.fn()
    const latestToggleBlockContext = vi.fn()

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
        onToggleBlockContext={oldToggleBlockContext}
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('[data-block-id="block_1_1"]')).not.toBeNull()
    })

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
        onToggleBlockContext={latestToggleBlockContext}
        activeBlockId={null}
        onBlockSelect={vi.fn()}
      />
    )

    const firstBlock = container.querySelector('[data-block-id="block_1_1"]')
    expect(firstBlock).not.toBeNull()

    const contextButton = within(firstBlock as HTMLElement).getByRole('button', {
      name: /add block to context/i,
    })

    fireEvent.click(contextButton)

    expect(oldToggleBlockContext).not.toHaveBeenCalled()
    expect(latestToggleBlockContext).toHaveBeenCalledWith('block_1_1', 1)
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
