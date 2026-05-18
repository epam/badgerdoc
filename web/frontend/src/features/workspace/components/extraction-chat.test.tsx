import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ExtractionChat } from './extraction-chat'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'

const { mutateAsync } = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
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

  it('clears the prompt after the trigger request succeeds', async () => {
    const { onPromptChange } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(onPromptChange).toHaveBeenCalledWith('')
    })
  })

  it('preserves the prompt when the trigger request fails', async () => {
    mutateAsync.mockRejectedValueOnce(new Error('trigger failed'))
    const { onPromptChange } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(onPromptChange).not.toHaveBeenCalledWith('')
  })

  it('shows a loading spinner in the send button while processing', () => {
    renderExtractionChat({ isProcessing: true })

    expect(screen.getByRole('button', { name: /send prompt/i })).toBeDisabled()
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('shows success feedback after the trigger request succeeds', async () => {
    renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(screen.getByRole('status', { name: /request sent/i })).toBeInTheDocument()
    })
  })

  it('unlocks and notifies the parent after the trigger request succeeds', async () => {
    const setIsRunningInference = vi.fn()
    const onTriggerSuccess = vi.fn()
    renderExtractionChat({ setIsRunningInference, onTriggerSuccess })

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(setIsRunningInference).toHaveBeenNthCalledWith(1, true)
    await waitFor(() => {
      expect(setIsRunningInference).toHaveBeenLastCalledWith(false)
    })
    expect(onTriggerSuccess).toHaveBeenCalledTimes(1)
  })

  it('does not notify the parent when the trigger request fails', async () => {
    mutateAsync.mockRejectedValueOnce(new Error('trigger failed'))
    const onTriggerSuccess = vi.fn()
    renderExtractionChat({ onTriggerSuccess })

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(onTriggerSuccess).not.toHaveBeenCalled()
  })
})
