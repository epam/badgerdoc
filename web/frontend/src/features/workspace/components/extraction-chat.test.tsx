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

function renderExtractionChat() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <ExtractionChat
        documentId="123"
        currentPage={1}
        prompt="Summarize this document"
        isWholeDocumentSelected={false}
        selectedPages={[]}
        onPromptChange={vi.fn()}
        registerPromptContextInserter={vi.fn()}
        onAddWholeDocument={vi.fn()}
        onAddCurrentPage={vi.fn()}
        activeTag="summary"
      />
    </QueryClientProvider>
  )
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
})
