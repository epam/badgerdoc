import type { ComponentProps } from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AgentLogsTab } from './agent-logs-tab'
import type { AgentLog } from '@/shared/api/badgerdoc/types'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'

const mocks = vi.hoisted(() => ({
  useAgentLogs: vi.fn(),
  fetchAgentLogs: vi.fn(),
}))
const originalScrollHeightDescriptor = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  'scrollHeight'
)

vi.mock('@/shared/api/hooks/use-agent-logs', () => ({
  useAgentLogs: mocks.useAgentLogs,
  fetchAgentLogs: mocks.fetchAgentLogs,
  mergeAgentLogs: (existingLogs: AgentLog[], incomingLogs: AgentLog[]) => {
    const logsById = new Map<string, AgentLog>()
    for (const log of [...existingLogs, ...incomingLogs]) {
      if (!logsById.has(String(log.id))) {
        logsById.set(String(log.id), log)
      }
    }

    return [...logsById.values()].sort((left, right) =>
      left.created_at.localeCompare(right.created_at)
    )
  },
}))

vi.mock('@/features/workspace/components/extraction-chat', () => ({
  ExtractionChat: ({
    prompt,
    onTriggerSuccess,
  }: {
    prompt: string
    onTriggerSuccess?: () => void
  }) => (
    <div aria-label="Agent prompt">
      <span>{prompt}</span>
      <button type="button" onClick={onTriggerSuccess}>
        Submit agent request
      </button>
    </div>
  ),
}))

function createAgentLog(id: number, createdAt: string, message: string): AgentLog {
  return {
    id,
    document: 123,
    task: null,
    level: 'INFO',
    source: 'Temporal',
    log: { message },
    created_at: createdAt,
  }
}

function createAgentLogsTabProps(
  overrides: Partial<ComponentProps<typeof AgentLogsTab>> = {}
): ComponentProps<typeof AgentLogsTab> {
  const workflowSelection = {
    workflows: [
      {
        id: 7,
        name: 'Test workflow',
        extractionScope: ['document', 'page'],
        supportPrompts: true,
      },
    ],
    isWorkflowsLoading: false,
    selectedWorkflowId: 7,
    setSelectedWorkflowId: vi.fn(),
    selectedWorkflow: {
      id: 7,
      name: 'Test workflow',
      extractionScope: ['document', 'page'],
      supportPrompts: true,
    },
    availableScopes: ['document', 'page'],
    canUseDocumentContext: true,
    canUsePageContext: true,
  } satisfies ChatWorkflowSelection

  return {
    documentId: '123',
    currentPage: 1,
    chatContext: {
      prompt: 'Review this document',
      isWholeDocumentSelected: false,
      selectedPages: [],
      selectedBlocks: [],
      onPromptChange: vi.fn(),
      registerPromptContextInserter: vi.fn(),
      onAddWholeDocument: vi.fn(),
      onAddCurrentPage: vi.fn(),
      onToggleBlock: vi.fn(),
    },
    workflowSelection,
    isRunningInference: false,
    setIsRunningInference: vi.fn(),
    onTriggerSuccess: vi.fn(),
    ...overrides,
  }
}

function renderAgentLogsTab(overrides: Partial<ComponentProps<typeof AgentLogsTab>> = {}) {
  return render(<AgentLogsTab {...createAgentLogsTabProps(overrides)} />)
}

describe('AgentLogsTab', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
    if (originalScrollHeightDescriptor) {
      Object.defineProperty(HTMLElement.prototype, 'scrollHeight', originalScrollHeightDescriptor)
    } else {
      Reflect.deleteProperty(HTMLElement.prototype, 'scrollHeight')
    }
  })

  it('renders a loading state while fetching logs', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    })

    renderAgentLogsTab()

    expect(screen.getByLabelText(/loading agent logs/i)).toBeInTheDocument()
    expect(mocks.useAgentLogs).toHaveBeenCalledWith({ documentId: '123', page: 1 })
  })

  it('renders an empty state when no logs are available', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: { count: 0, next: null, previous: null, results: [] },
      isLoading: false,
      isError: false,
    })

    renderAgentLogsTab()

    expect(screen.getByRole('heading', { name: /no agent logs yet/i })).toBeInTheDocument()
  })

  it('renders the shared chat input area below the logs area', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: { count: 0, next: null, previous: null, results: [] },
      isLoading: false,
      isError: false,
    })

    renderAgentLogsTab()

    expect(screen.getByLabelText(/agent prompt/i)).toHaveTextContent('Review this document')
  })

  it('renders an error state when logs fail to load', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    })

    renderAgentLogsTab()

    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load agent logs/i)
  })

  it('renders logs in the order returned by the normalized API hook', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 2,
        next: null,
        previous: null,
        results: [
          createAgentLog(1, '2026-05-18T10:00:00Z', 'First log'),
          createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
        ],
      },
      isLoading: false,
      isError: false,
    })

    renderAgentLogsTab()

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('First log')
    expect(items[1]).toHaveTextContent('Second log')
    expect(items[0]).not.toHaveClass('agent-log-entry--new')
    expect(items[1]).not.toHaveClass('agent-log-entry--new')
  })

  it('scrolls to the latest logs after the initial page loads', () => {
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 2,
        next: null,
        previous: null,
        results: [
          createAgentLog(1, '2026-05-18T10:00:00Z', 'First log'),
          createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
        ],
      },
      isLoading: false,
      isError: false,
    })

    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      value: 900,
    })

    renderAgentLogsTab()

    expect(screen.getByLabelText(/agent log timeline/i).scrollTop).toBe(900)
  })

  it('scrolls to the latest logs after the first page is reloaded', () => {
    const firstPage = {
      count: 1,
      next: null,
      previous: null,
      results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
    }
    const reloadedPage = {
      count: 2,
      next: null,
      previous: null,
      results: [
        createAgentLog(1, '2026-05-18T10:00:00Z', 'First log'),
        createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
      ],
    }
    let queryData = firstPage
    mocks.useAgentLogs.mockImplementation(() => ({
      data: queryData,
      isLoading: false,
      isError: false,
    }))

    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      value: 1200,
    })

    const { rerender } = renderAgentLogsTab()
    const timeline = screen.getByLabelText(/agent log timeline/i)
    timeline.scrollTop = 0

    queryData = reloadedPage
    rerender(<AgentLogsTab {...createAgentLogsTabProps()} />)

    expect(timeline.scrollTop).toBe(1200)
    const items = screen.getAllByRole('listitem')
    expect(items[0]).not.toHaveClass('agent-log-entry--new')
    expect(items[1]).toHaveClass('agent-log-entry--new')
  })

  it('polls for new logs after the latest known timestamp', async () => {
    vi.useFakeTimers()
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        createAgentLog(1, '2026-05-18T10:00:00Z', 'First log again'),
        createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
      ],
    })

    renderAgentLogsTab()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    expect(mocks.fetchAgentLogs).toHaveBeenCalledWith({
      documentId: '123',
      after: '2026-05-18T10:00:00Z',
    })
    expect(screen.getByText('Second log')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).not.toHaveClass('agent-log-entry--new')
    expect(items[1]).toHaveClass('agent-log-entry--new')
  })

  it('clears the new-log animation marker after the reveal window', async () => {
    vi.useFakeTimers()
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log')],
    })

    renderAgentLogsTab()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    const newItem = screen.getAllByRole('listitem')[1]
    expect(newItem).toHaveClass('agent-log-entry--new')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(700)
    })

    expect(newItem).not.toHaveClass('agent-log-entry--new')
  })

  it('keeps the timeline pinned to the bottom when polling appends logs near the bottom', async () => {
    vi.useFakeTimers()
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log')],
    })

    renderAgentLogsTab()

    const timeline = screen.getByLabelText(/agent log timeline/i)
    Object.defineProperty(timeline, 'scrollHeight', {
      configurable: true,
      value: 1000,
    })
    Object.defineProperty(timeline, 'clientHeight', {
      configurable: true,
      value: 400,
    })
    timeline.scrollTop = 520

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    expect(timeline.scrollTop).toBe(1000)
  })

  it('does not pull the timeline to the bottom when polling appends logs while reading older logs', async () => {
    vi.useFakeTimers()
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log')],
    })

    renderAgentLogsTab()

    const timeline = screen.getByLabelText(/agent log timeline/i)
    Object.defineProperty(timeline, 'scrollHeight', {
      configurable: true,
      value: 1000,
    })
    Object.defineProperty(timeline, 'clientHeight', {
      configurable: true,
      value: 400,
    })
    timeline.scrollTop = 100

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    expect(timeline.scrollTop).toBe(100)
  })

  it('keeps existing logs visible during polling errors and retries later', async () => {
    vi.useFakeTimers()
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce({
      count: 2,
      next: null,
      previous: null,
      results: [createAgentLog(2, '2026-05-18T10:01:00Z', 'Recovered log')],
    })

    renderAgentLogsTab()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    expect(screen.getByText('First log')).toBeInTheDocument()
    expect(screen.getByText(/live updates are temporarily unavailable/i)).toBeInTheDocument()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500)
    })

    expect(screen.getByText('Recovered log')).toBeInTheDocument()
    expect(screen.queryByText(/live updates are temporarily unavailable/i)).not.toBeInTheDocument()
  })

  it('loads older logs when scrolling near the top and prepends them', async () => {
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 3,
        next: '?page=2',
        previous: null,
        results: [
          createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
          createAgentLog(3, '2026-05-18T10:02:00Z', 'Third log'),
        ],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockResolvedValue({
      count: 3,
      next: null,
      previous: '?page=1',
      results: [
        createAgentLog(1, '2026-05-18T10:00:00Z', 'First log'),
        createAgentLog(2, '2026-05-18T10:01:00Z', 'Duplicate second log'),
      ],
    })

    renderAgentLogsTab()

    await act(async () => {
      fireEvent.scroll(screen.getByLabelText(/agent log timeline/i), {
        target: { scrollTop: 0 },
      })
    })

    expect(mocks.fetchAgentLogs).toHaveBeenCalledWith({ documentId: '123', page: 2 })

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent('First log')
    expect(items[1]).toHaveTextContent('Second log')
    expect(items[2]).toHaveTextContent('Third log')
    expect(items[0]).not.toHaveClass('agent-log-entry--new')
    expect(items[1]).not.toHaveClass('agent-log-entry--new')
    expect(items[2]).not.toHaveClass('agent-log-entry--new')
  })

  it('preserves scroll position after older logs are prepended', async () => {
    let scrollHeight = 1000
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 3,
        next: '?page=2',
        previous: null,
        results: [
          createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
          createAgentLog(3, '2026-05-18T10:02:00Z', 'Third log'),
        ],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockImplementation(async () => {
      scrollHeight = 1400
      return {
        count: 3,
        next: null,
        previous: '?page=1',
        results: [createAgentLog(1, '2026-05-18T10:00:00Z', 'First log')],
      }
    })

    renderAgentLogsTab()

    const timeline = screen.getByLabelText(/agent log timeline/i)
    Object.defineProperty(timeline, 'scrollHeight', {
      configurable: true,
      get: () => scrollHeight,
    })
    Object.defineProperty(timeline, 'scrollTop', {
      configurable: true,
      writable: true,
      value: 20,
    })

    await act(async () => {
      fireEvent.scroll(timeline, {
        target: { scrollTop: 20 },
      })
    })

    expect(timeline.scrollTop).toBe(420)
  })

  it('prevents parallel older log page requests', async () => {
    mocks.useAgentLogs.mockReturnValue({
      data: {
        count: 3,
        next: '?page=2',
        previous: null,
        results: [
          createAgentLog(2, '2026-05-18T10:01:00Z', 'Second log'),
          createAgentLog(3, '2026-05-18T10:02:00Z', 'Third log'),
        ],
      },
      isLoading: false,
      isError: false,
    })
    mocks.fetchAgentLogs.mockReturnValue(new Promise(() => undefined))

    renderAgentLogsTab()

    const timeline = screen.getByLabelText(/agent log timeline/i)
    await act(async () => {
      fireEvent.scroll(timeline, { target: { scrollTop: 0 } })
      fireEvent.scroll(timeline, { target: { scrollTop: 0 } })
    })

    expect(mocks.fetchAgentLogs).toHaveBeenCalledTimes(1)
  })
})
