import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ViewerToolbar } from './viewer-toolbar'
import { NEXT_BTN_ID, PREV_BTN_ID } from './config'

describe('ViewerToolbar', () => {
  it('keeps the page context action visible for single-page documents without showing pagination', () => {
    render(
      <ViewerToolbar
        isLoading={false}
        totalPages={1}
        currentPage={1}
        onNextClick={vi.fn()}
        onPrevClick={vi.fn()}
        onFitToPage={vi.fn()}
        isEditMode={false}
        onToggleEditMode={vi.fn()}
        onDownloadOriginal={vi.fn()}
        isDownloading={false}
        pageChatContext={{
          canAddCurrentPageToContext: true,
          onAddCurrentPageToContext: vi.fn(),
        }}
      />
    )

    expect(screen.getByRole('button', { name: /add page to context/i })).toBeInTheDocument()
    expect(document.getElementById(PREV_BTN_ID)).toBeNull()
    expect(document.getElementById(NEXT_BTN_ID)).toBeNull()
  })

  it('disables the page context action when prompt context is unavailable', () => {
    const onAddCurrentPageToContext = vi.fn()

    render(
      <ViewerToolbar
        isLoading={false}
        totalPages={1}
        currentPage={1}
        onNextClick={vi.fn()}
        onPrevClick={vi.fn()}
        onFitToPage={vi.fn()}
        isEditMode={false}
        onToggleEditMode={vi.fn()}
        onDownloadOriginal={vi.fn()}
        isDownloading={false}
        pageChatContext={{
          canAddCurrentPageToContext: true,
          isCurrentPageContextDisabled: true,
          currentPageContextTooltip: 'Prompt context is unavailable while you have unsaved changes.',
          onAddCurrentPageToContext,
        }}
      />
    )

    const addPageButton = screen.getByRole('button', { name: /add page to context/i })
    expect(addPageButton).toBeDisabled()

    fireEvent.click(addPageButton)
    expect(onAddCurrentPageToContext).not.toHaveBeenCalled()
  })
})
