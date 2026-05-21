import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ViewerToolbar } from './viewer-toolbar'
import { NEXT_BTN_ID, PREV_BTN_ID } from './config'

describe('ViewerToolbar', () => {
  it('shows the document context action and calls the shared handler', () => {
    const onAddWholeDocumentToContext = vi.fn()

    render(
      <ViewerToolbar
        isLoading={false}
        totalPages={3}
        currentPage={1}
        onNextClick={vi.fn()}
        onPrevClick={vi.fn()}
        onFitToPage={vi.fn()}
        isEditMode={false}
        onToggleEditMode={vi.fn()}
        onDownloadOriginal={vi.fn()}
        isDownloading={false}
        pageChatContext={{
          canAddWholeDocumentToContext: true,
          onAddWholeDocumentToContext,
        }}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: /add document to context/i }))

    expect(onAddWholeDocumentToContext).toHaveBeenCalledTimes(1)
  })

  it('places the document context action after the page context action', () => {
    render(
      <ViewerToolbar
        isLoading={false}
        totalPages={3}
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
          canAddWholeDocumentToContext: true,
          onAddWholeDocumentToContext: vi.fn(),
        }}
      />
    )

    const addPageButton = screen.getByRole('button', { name: /add page to context/i })
    const addDocumentButton = screen.getByRole('button', { name: /add document to context/i })

    expect(
      addPageButton.compareDocumentPosition(addDocumentButton) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })

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
          currentPageContextTooltip:
            'Prompt context is unavailable while you have unsaved changes.',
          onAddCurrentPageToContext,
        }}
      />
    )

    const addPageButton = screen.getByRole('button', { name: /add page to context/i })
    expect(addPageButton).toBeDisabled()

    fireEvent.click(addPageButton)
    expect(onAddCurrentPageToContext).not.toHaveBeenCalled()
  })

  it('disables the document context action when prompt context is unavailable', () => {
    const onAddWholeDocumentToContext = vi.fn()

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
          canAddWholeDocumentToContext: true,
          isWholeDocumentContextDisabled: true,
          wholeDocumentContextTooltip:
            'Prompt context is unavailable while you have unsaved changes.',
          onAddWholeDocumentToContext,
        }}
      />
    )

    const addDocumentButton = screen.getByRole('button', { name: /add document to context/i })
    expect(addDocumentButton).toBeDisabled()

    fireEvent.click(addDocumentButton)
    expect(onAddWholeDocumentToContext).not.toHaveBeenCalled()
  })
})
