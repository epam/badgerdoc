import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ExtractionChat } from './extraction-chat'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'

const { mutateAsync, workflowStatusState } = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  workflowStatusState: {
    data: null as null | { status: string },
  },
}))

vi.mock('@/shared/api/hooks/use-workflows', () => ({
  useChatWorkflows: () => ({
    data: [
      {
        id: 7,
        name: 'Test workflow',
        extractionScope: [],
        supportPrompts: true,
        tags: ['summary'],
      },
    ],
    isLoading: false,
  }),
  useTriggerWorkflow: () => ({
    mutateAsync,
    isPending: false,
  }),
  useWorkflowStatus: () => ({
    data: workflowStatusState.data,
  }),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('./prompt-context-editor', () => ({
  PromptContextEditor: ({
    value,
    onChange,
  }: {
    value: string
    onChange: (value: string) => void
  }) => (
    <textarea aria-label="Prompt editor" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}))

function renderExtractionChat(props: Partial<React.ComponentProps<typeof ExtractionChat>> = {}) {
  const onPromptChange = vi.fn()
  const workflowSelection = {
    workflows: [
      {
        id: 7,
        name: 'Test workflow',
        extractionScope: [],
        supportPrompts: true,
        tags: ['summary'],
      },
    ],
    isWorkflowsLoading: false,
    selectedWorkflowId: 7,
    setSelectedWorkflowId: vi.fn(),
    selectedWorkflow: {
      id: 7,
      name: 'Test workflow',
      extractionScope: [],
      supportPrompts: true,
      tags: ['summary'],
    },
    availableScopes: [],
    canUseDocumentContext: false,
    canUsePageContext: false,
  } satisfies ChatWorkflowSelection
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  const getUi = (nextProps: Partial<React.ComponentProps<typeof ExtractionChat>> = props) => (
    <QueryClientProvider client={queryClient}>
      <ExtractionChat
        documentId="123"
        currentPage={1}
        prompt="Summarize this document"
        isWholeDocumentSelected={false}
        selectedPages={[]}
        onPromptChange={onPromptChange}
        registerPromptContextInserter={vi.fn()}
        onAddWholeDocument={vi.fn()}
        onAddCurrentPage={vi.fn()}
        activeTag="summary"
        workflowSelection={workflowSelection}
        {...nextProps}
      />
    </QueryClientProvider>
  )
  const renderResult = render(getUi())

  return {
    onPromptChange,
    rerenderExtractionChat: (
      nextProps: Partial<React.ComponentProps<typeof ExtractionChat>> = props
    ) => renderResult.rerender(getUi(nextProps)),
    ...renderResult,
  }
}

describe('ExtractionChat', () => {
  beforeEach(() => {
    mutateAsync.mockReset()
    mutateAsync.mockResolvedValue({ workflow_id: 'wf-1' })
    workflowStatusState.data = null
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('allows sending a plain prompt without context chips', async () => {
    renderExtractionChat()

    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeEnabled()

    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: 7,
        payload: {
          document_id: 123,
          llm_params: 'Summarize this document',
        },
      })
    })
  })

  it('keeps the prompt draft while the workflow is still running', async () => {
    const { onPromptChange } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(onPromptChange).not.toHaveBeenCalled()
  })

  it('clears the prompt after the workflow finishes', async () => {
    const { onPromptChange, rerenderExtractionChat } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    workflowStatusState.data = { status: 'Finished' }
    rerenderExtractionChat()

    await waitFor(() => {
      expect(onPromptChange).toHaveBeenCalledWith('')
    })
  })

  it('preserves the prompt when the workflow fails', async () => {
    const { onPromptChange, rerenderExtractionChat } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    workflowStatusState.data = { status: 'Failed' }
    rerenderExtractionChat()

    await act(async () => {
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)))
    })

    expect(onPromptChange).not.toHaveBeenCalledWith('')
  })

  it('shows a loading spinner in the send button while processing', () => {
    renderExtractionChat({ isProcessing: true })

    expect(screen.getByRole('button', { name: /send prompt/i })).toBeDisabled()
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('shows success feedback only after the workflow finishes', async () => {
    const { rerenderExtractionChat } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(screen.queryByRole('status', { name: /extraction updated/i })).not.toBeInTheDocument()

    workflowStatusState.data = { status: 'Finished' }
    rerenderExtractionChat()

    await waitFor(() => {
      expect(screen.getByRole('status', { name: /extraction updated/i })).toBeInTheDocument()
    })
  })
})
