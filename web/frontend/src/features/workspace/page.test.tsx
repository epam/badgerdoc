import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { WorkspacePage } from './page'

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  invalidateQueries: vi.fn(),
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
  CollectionViewer: () => <section>Viewer</section>,
}))

vi.mock('@/components/not-found', () => ({
  DocumentNotFoundPage: () => <div>Document not found</div>,
  TaskNotFoundPage: () => <div>Task not found</div>,
}))

vi.mock('@/shared/api/hooks', () => ({
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

vi.mock('@/features/workspace/hooks/use-extraction-state', () => ({
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

vi.mock('@/features/workspace/hooks/use-extraction-api', () => ({
  useExtractionApi: () => ({
    saveExtractionPages: vi.fn(),
    acceptExtraction: vi.fn(),
    isPending: false,
  }),
}))

vi.mock('@/features/workspace/hooks/use-reload-draft-autosave', () => ({
  useReloadDraftAutosave: vi.fn(),
}))

vi.mock('@/features/workspace/hooks/use-extraction-chat-context', () => ({
  useExtractionChatContext: () => ({
    prompt: '',
    isWholeDocumentSelected: false,
    selectedPages: [],
    selectedBlocks: [],
    setPrompt: vi.fn(),
    registerPromptContextInserter: vi.fn(),
    addWholeDocument: vi.fn(),
    togglePage: vi.fn(),
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
  useViewerChatContext: () => ({}),
}))

vi.mock('@/features/workspace/components/document-overview-popover', () => ({
  DocumentOverviewPopover: () => <button type="button">Overview</button>,
}))

vi.mock('@/features/workspace/components/extraction-results-tab.tsx', () => ({
  ExtractionResultsTab: ({ onTriggerSuccess }: { onTriggerSuccess?: () => void }) => (
    <button type="button" onClick={onTriggerSuccess}>
      Trigger success
    </button>
  ),
}))

vi.mock('@/features/workspace/components/agent-logs-tab', () => ({
  AgentLogsTab: ({ onTriggerSuccess }: { onTriggerSuccess?: () => void }) => (
    <div>
      <div>Agent logs</div>
      <button type="button" onClick={onTriggerSuccess}>
        Submit from Agent
      </button>
    </div>
  ),
}))

describe('WorkspacePage Agent submit integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.searchTag = 'summary'
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
})
