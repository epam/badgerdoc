import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { WorkspacePage } from './page'

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  invalidateQueries: vi.fn(),
  isFetching: vi.fn(),
  addWholeDocument: vi.fn(),
  togglePage: vi.fn(),
  useViewerChatContext: vi.fn(),
  searchTag: 'summary',
}))

vi.mock('@tanstack/react-router', () => ({
  useParams: () => ({ id: '123' }),
  useNavigate: () => mocks.navigate,
  useSearch: () => ({ tag: mocks.searchTag }),
  useMatches: () => [{ routeId: '/documents/$id' }],
}))

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: mocks.invalidateQueries,
    isFetching: mocks.isFetching,
  }),
}))

vi.mock('@/design-system/patterns/split-view', () => ({
  SplitView: ({ left, right }: { left: React.ReactNode; right: React.ReactNode }) => (
    <div>
      <div>{left}</div>
      <div>{right}</div>
    </div>
  ),
}))

vi.mock('@/components/document-header', () => ({
  DocumentHeader: ({
    children,
    titleActions,
  }: {
    children?: React.ReactNode
    titleActions?: React.ReactNode
  }) => (
    <header>
      {titleActions}
      {children}
    </header>
  ),
}))

vi.mock('@/components/document-hierarchy-popover', () => ({
  DocumentHierarchyPopover: () => <button type="button">Hierarchy</button>,
}))

vi.mock('@/components/collection-viewer/collection-viewer', () => ({
  CollectionViewer: ({
    pageChatContext,
  }: {
    pageChatContext?: {
      canAddWholeDocumentToContext?: boolean
      isWholeDocumentContextDisabled?: boolean
      onAddWholeDocumentToContext?: () => void
      canAddCurrentPageToContext?: boolean
      isCurrentPageContextDisabled?: boolean
      onAddCurrentPageToContext?: () => void
    }
  }) => (
    <section>
      Viewer
      {pageChatContext?.canAddCurrentPageToContext && (
        <button
          type="button"
          disabled={pageChatContext.isCurrentPageContextDisabled}
          onClick={pageChatContext.onAddCurrentPageToContext}
        >
          Add page to context
        </button>
      )}
      {pageChatContext?.canAddWholeDocumentToContext && (
        <button
          type="button"
          disabled={pageChatContext.isWholeDocumentContextDisabled}
          onClick={pageChatContext.onAddWholeDocumentToContext}
        >
          Add document to context
        </button>
      )}
    </section>
  ),
}))

vi.mock('@/components/not-found', () => ({
  DocumentNotFoundPage: () => <div>Document not found</div>,
  TaskNotFoundPage: () => <div>Task not found</div>,
}))

vi.mock('@/shared/api/hooks', () => ({
  extractionPagesKeys: {
    documentWithTags: (documentId: string, tags?: string) => [
      'badgerdoc-extraction-pages',
      documentId,
      tags,
    ],
  },
  useWorkspaceDocument: () => ({
    data: {
      id: '123',
      title: 'Current document',
      type: 'article',
      authors: [],
      publicationDate: '2026-05-18',
      createdAt: '2026-05-18T10:00:00Z',
      updatedAt: '2026-05-18T10:00:00Z',
      uploadedBy: 'owner',
      parentDocumentId: null,
      pdfUrl: 'https://example.test/doc.pdf',
      metadata: {},
      tags: [],
      status: 'pending_review',
      abstract: '',
    },
    isLoading: false,
    isError: false,
    error: null,
  }),
  useTask: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
  }),
  useBadgerDocExtractionPages: () => ({
    data: [],
    isLoading: false,
  }),
  useTags: () => ({
    data: [{ tag: 'summary', literal: 'Summary', order: 1 }],
    isLoading: false,
  }),
}))

vi.mock('@/shared/api/hooks/use-tasks', () => ({
  useTasksQueue: () => ({
    data: null,
    isLoading: false,
  }),
}))

vi.mock('@/features/workspace/hooks/extraction-state', () => ({
  useExtractionState: () => ({
    currentPage: 1,
    setCurrentPage: vi.fn(),
    activeBlockId: null,
    setActiveBlockId: vi.fn(),
    hasChanges: false,
    highlights: {},
    pendingPayload: [],
    onBaselineReady: vi.fn(),
    onContentChange: vi.fn(),
    onBlockDelete: vi.fn(),
    revertChanges: vi.fn(),
    acceptChanges: vi.fn(),
    scopedExtractionPages: [],
    handleBlockBoundingBoxUpdate: vi.fn(),
    handleBlockCreate: vi.fn(),
    createdBlockIds: new Set(),
    deletedBlockIds: [],
  }),
}))

vi.mock('@/features/workspace/hooks/extraction-api', () => ({
  useExtractionApi: () => ({
    saveExtractionPages: vi.fn(),
    acceptExtraction: vi.fn(),
    isPending: false,
  }),
}))

vi.mock('@/features/workspace/hooks/use-reload-draft-autosave', () => ({
  useReloadDraftAutosave: vi.fn(),
}))

vi.mock('@/features/workspace/hooks/extraction-chat-context', () => ({
  useExtractionChatContext: () => ({
    prompt: '',
    isWholeDocumentSelected: false,
    selectedPages: [],
    selectedBlocks: [],
    setPrompt: vi.fn(),
    registerPromptContextInserter: vi.fn(),
    addWholeDocument: mocks.addWholeDocument,
    togglePage: mocks.togglePage,
    toggleBlock: vi.fn(),
    removeBlocks: vi.fn(),
  }),
}))

vi.mock('@/features/workspace/hooks/use-chat-workflow-selection', () => ({
  useChatWorkflowSelection: () => ({
    workflows: [],
    isWorkflowsLoading: false,
    selectedWorkflowId: null,
    setSelectedWorkflowId: vi.fn(),
    selectedWorkflow: null,
    availableScopes: [],
    canUseDocumentContext: false,
    canUsePageContext: false,
  }),
}))

vi.mock('@/features/workspace/hooks/use-viewer-chat-context', () => ({
  useViewerChatContext: (params: {
    canAddContext: boolean
    workflowSelection: {
      canUseDocumentContext: boolean
      canUsePageContext: boolean
      isWorkflowsLoading: boolean
    }
    onAddWholeDocument: () => void
    onAddCurrentPage: () => void
  }) => {
    mocks.useViewerChatContext(params)

    return {
      canAddWholeDocumentToContext: params.canAddContext,
      isWholeDocumentContextDisabled:
        params.workflowSelection.isWorkflowsLoading ||
        !params.workflowSelection.canUseDocumentContext,
      onAddWholeDocumentToContext: params.onAddWholeDocument,
      canAddCurrentPageToContext: params.canAddContext,
      isCurrentPageContextDisabled:
        params.workflowSelection.isWorkflowsLoading || !params.workflowSelection.canUsePageContext,
      onAddCurrentPageToContext: params.onAddCurrentPage,
    }
  },
}))

vi.mock('@/features/workspace/components/document-overview', () => ({
  DocumentOverviewPopover: () => <button type="button">Overview</button>,
}))

vi.mock('@/features/workspace/components/extraction-results-tab', () => ({
  ExtractionResultsTab: ({ onTriggerSuccess }: { onTriggerSuccess?: () => void }) => (
    <button type="button" onClick={onTriggerSuccess}>
      Trigger success
    </button>
  ),
}))

vi.mock('@/features/workspace/components/agent-logs', () => ({
  AgentLogsTab: ({
    onTriggerSuccess,
    workflowSelection,
  }: {
    onTriggerSuccess?: () => void
    workflowSelection?: {
      canUseDocumentContext: boolean
      canUsePageContext: boolean
    }
  }) => (
    <div>
      <div>Agent logs</div>
      <div>
        Agent scopes: {workflowSelection?.canUseDocumentContext ? 'document' : 'no-document'}{' '}
        {workflowSelection?.canUsePageContext ? 'page' : 'no-page'}
      </div>
      <button type="button" onClick={onTriggerSuccess}>
        Submit from Agent
      </button>
    </div>
  ),
}))

describe('WorkspacePage Agent submit integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.isFetching.mockReturnValue(0)
    mocks.searchTag = 'summary'
  })

  it('does not refresh extraction data on ordinary extraction tab activation', () => {
    render(<WorkspacePage />)

    expect(mocks.invalidateQueries).not.toHaveBeenCalledWith({
      queryKey: ['badgerdoc-extraction-pages', '123', 'summary'],
      exact: true,
    })
  })

  it('refreshes extraction data after Agent submit success when returning to an extraction tab', async () => {
    mocks.searchTag = 'agent'
    const { rerender } = render(<WorkspacePage />)

    fireEvent.click(screen.getByRole('button', { name: /submit from agent/i }))
    mocks.invalidateQueries.mockClear()

    mocks.searchTag = 'summary'
    rerender(<WorkspacePage />)

    await waitFor(() =>
      expect(mocks.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['badgerdoc-extraction-pages', '123', 'summary'],
        exact: true,
      })
    )
  })

  it('refreshes the same extraction tab after submit success, leaving, and returning', async () => {
    const { rerender } = render(<WorkspacePage />)

    fireEvent.click(screen.getByRole('button', { name: /trigger success/i }))
    mocks.invalidateQueries.mockClear()

    mocks.searchTag = 'agent'
    rerender(<WorkspacePage />)
    mocks.invalidateQueries.mockClear()

    mocks.searchTag = 'summary'
    rerender(<WorkspacePage />)

    await waitFor(() =>
      expect(mocks.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['badgerdoc-extraction-pages', '123', 'summary'],
        exact: true,
      })
    )
  })

  it('does not duplicate-invalidate the same tab on rerender', () => {
    const { rerender } = render(<WorkspacePage />)

    rerender(<WorkspacePage />)

    expect(mocks.invalidateQueries).not.toHaveBeenCalledWith({
      queryKey: ['badgerdoc-extraction-pages', '123', 'summary'],
      exact: true,
    })
  })

  it('does not duplicate-refresh an extraction tab that is already fetching', () => {
    mocks.isFetching.mockReturnValue(1)

    const { rerender } = render(<WorkspacePage />)

    fireEvent.click(screen.getByRole('button', { name: /trigger success/i }))
    mocks.invalidateQueries.mockClear()

    mocks.searchTag = 'agent'
    rerender(<WorkspacePage />)
    mocks.searchTag = 'summary'
    rerender(<WorkspacePage />)

    expect(mocks.invalidateQueries).not.toHaveBeenCalledWith({
      queryKey: ['badgerdoc-extraction-pages', '123', 'summary'],
      exact: true,
    })
  })

  it('refreshes Agent logs when switching back to the Agent tab', async () => {
    const { rerender } = render(<WorkspacePage />)

    mocks.invalidateQueries.mockClear()

    mocks.searchTag = 'agent'
    rerender(<WorkspacePage />)

    await waitFor(() =>
      expect(mocks.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['badgerdoc-agent-logs', '123', { after: undefined, page: 1 }],
      })
    )
  })

  it('does not refresh Agent logs on ordinary Agent tab rerender', () => {
    mocks.searchTag = 'agent'
    const { rerender } = render(<WorkspacePage />)

    rerender(<WorkspacePage />)

    expect(mocks.invalidateQueries).not.toHaveBeenCalledWith({
      queryKey: ['badgerdoc-agent-logs', '123', { after: undefined, page: 1 }],
    })
  })

  it('switches to Agent and invalidates the first Agent log page after contextual submit success', () => {
    render(<WorkspacePage />)

    fireEvent.click(screen.getByRole('button', { name: /trigger success/i }))

    expect(mocks.navigate).toHaveBeenCalledWith({
      to: '/documents/$id',
      params: { id: '123' },
      search: { tag: 'agent' },
      replace: true,
    })
    expect(mocks.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['badgerdoc-agent-logs', '123', { after: undefined, page: 1 }],
    })
  })

  it('stays on Agent and invalidates the first Agent log page after Agent tab submit success', () => {
    mocks.searchTag = 'agent'

    render(<WorkspacePage />)

    fireEvent.click(screen.getByRole('button', { name: /submit from agent/i }))

    expect(mocks.navigate).toHaveBeenCalledWith({
      to: '/documents/$id',
      params: { id: '123' },
      search: { tag: 'agent' },
      replace: true,
    })
    expect(mocks.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['badgerdoc-agent-logs', '123', { after: undefined, page: 1 }],
    })
  })

  it('enables document and page context controls on the Agent tab', () => {
    mocks.searchTag = 'agent'

    render(<WorkspacePage />)

    expect(screen.getByText(/Agent scopes: document page/i)).toBeInTheDocument()

    const addPageButton = screen.getByRole('button', { name: /add page to context/i })
    const addDocumentButton = screen.getByRole('button', { name: /add document to context/i })
    expect(addPageButton).toBeEnabled()
    expect(addDocumentButton).toBeEnabled()

    fireEvent.click(addPageButton)
    fireEvent.click(addDocumentButton)

    expect(mocks.togglePage).toHaveBeenCalledWith(1)
    expect(mocks.addWholeDocument).toHaveBeenCalledTimes(1)
    expect(mocks.useViewerChatContext).toHaveBeenCalledWith(
      expect.objectContaining({
        canAddContext: true,
        workflowSelection: expect.objectContaining({
          canUseDocumentContext: true,
          canUsePageContext: true,
        }),
      })
    )
  })
})
