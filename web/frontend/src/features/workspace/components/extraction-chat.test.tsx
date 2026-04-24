import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ExtractionChat } from './extraction-chat'

const mutateAsync = vi.fn()

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
    data: null,
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
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  const renderResult = render(
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
        {...props}
      />
    </QueryClientProvider>
  )

  return {
    onPromptChange,
    ...renderResult,
  }
}

describe('ExtractionChat', () => {
  beforeEach(() => {
    mutateAsync.mockReset()
    mutateAsync.mockResolvedValue({ workflow_id: 'wf-1' })
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

  it('keeps the prompt draft after a successful send', async () => {
    const { onPromptChange } = renderExtractionChat()

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1)
    })

    expect(onPromptChange).not.toHaveBeenCalled()
  })

  it('shows a loading spinner in the send button while processing', () => {
    renderExtractionChat({ isProcessing: true })

    expect(screen.getByRole('button', { name: /send prompt/i })).toBeDisabled()
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })
})
