import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AgentLogEntry } from './agent-log-entry'
import type { AgentLog } from '@/shared/api/badgerdoc/types'

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useWorkspaceDocument: vi.fn(),
}))

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mocks.navigate,
}))

vi.mock('@/shared/api/hooks/use-document-workspace', () => ({
  useWorkspaceDocument: mocks.useWorkspaceDocument,
}))

function createLog(log: AgentLog['log'], overrides: Partial<AgentLog> = {}): AgentLog {
  return {
    id: 1,
    document: 123,
    task: null,
    level: 'INFO',
    source: 'Temporal',
    log,
    created_at: '2026-05-18T10:00:00Z',
    ...overrides,
  }
}

describe('AgentLogEntry', () => {
  it('renders supported payload fields in stable order', () => {
    const { container } = render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: { model: 'test' },
            code: 'const ok = true',
            markdown: '**Markdown** value',
            message: 'Plain message',
          })}
        />
      </ol>
    )

    const labels = Array.from(container.querySelectorAll('.uppercase')).map(
      (node) => node.textContent
    )
    expect(labels).toEqual(['Message', 'Markdown', 'Code', 'Workflow details'])
    expect(screen.getByText('Plain message')).toBeInTheDocument()
    expect(screen.getAllByText('Markdown').find((node) => node.tagName === 'STRONG')).toHaveClass(
      'font-semibold'
    )
    expect(screen.getByText(/const ok = true/)).toBeInTheDocument()
    expect(screen.getByText('model:')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
  })

  it('renders markdown without executing raw HTML', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({ markdown: '<script>alert("x")</script> **safe**' })} />
      </ol>
    )

    expect(screen.getByText(/<script>alert\("x"\)<\/script>/)).toBeInTheDocument()
    expect(screen.getByText('safe')).toHaveClass('font-semibold')
    expect(document.querySelector('script')).not.toBeInTheDocument()
  })

  it('renders missing payloads without crashing', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({})} />
      </ol>
    )

    expect(screen.getByText(/no payload details/i)).toBeInTheDocument()
  })

  it('renders supported blank string payload fields', () => {
    const { container } = render(
      <ol>
        <AgentLogEntry log={createLog({ message: '', markdown: '', code: '' })} />
      </ol>
    )

    const labels = Array.from(container.querySelectorAll('.uppercase')).map(
      (node) => node.textContent
    )
    expect(labels).toEqual(['Message', 'Markdown', 'Code'])
    expect(screen.queryByText(/no payload details/i)).not.toBeInTheDocument()
  })

  it.each([
    ['null', null],
    ['empty object', {}],
    ['empty array', []],
    ['empty string', ''],
    ['blank string', '   '],
  ])('hides empty workflow params when value is %s', (_label, workflowParams) => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            message: 'Workflow completed',
            workflow_params: workflowParams,
          })}
        />
      </ol>
    )

    expect(screen.getByText('Workflow completed')).toBeInTheDocument()
    expect(screen.queryByText(/workflow params/i)).not.toBeInTheDocument()
  })

  it('renders llm params as readable prompt-like text', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              llm_params: 'First line\n  indented second line',
            },
          })}
        />
      </ol>
    )

    expect(screen.getByText('User input')).toBeInTheDocument()
    expect(screen.queryByText('llm_params')).not.toBeInTheDocument()
    expect(screen.queryByText('Workflow details')).not.toBeInTheDocument()

    const promptBlock = screen.getByText(/First line/)
    expect(promptBlock.textContent).toBe('First line\n  indented second line')
    expect(promptBlock.tagName).not.toBe('CODE')
    expect(promptBlock.closest('pre')).not.toBeInTheDocument()
  })

  it('renders llm params only once as user input before workflow details', () => {
    const { container } = render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              workflow: { name: 'Mineru OCR', trigger: 'manual' },
              llm_params: '{{/badgerdoc/document/345/}}',
              linked_documents: [345],
            },
          })}
        />
      </ol>
    )

    const labels = Array.from(container.querySelectorAll('.uppercase')).map(
      (node) => node.textContent
    )
    expect(labels).toEqual(['User input', 'Workflow details'])
    expect(screen.queryByText('llm_params')).not.toBeInTheDocument()
    expect(screen.getByText('Document')).toBeInTheDocument()
    expect(screen.getByText('workflow')).toBeInTheDocument()
    expect(screen.getByText('linked_documents')).toBeInTheDocument()
  })

  it('renders llm params context links as read-only chips while preserving text', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              llm_params:
                'Please analyze {{/badgerdoc/document/345/}} and compare it with {{/badgerdoc/document/777/page/2/}}',
            },
          })}
        />
      </ol>
    )

    const promptBlock = screen.getByText(/Please analyze/)
    expect(promptBlock).toHaveTextContent('Please analyze Document and compare it with Page 2')
    expect(screen.getByText('Document')).toHaveClass('truncate')
    expect(screen.getByText('Page 2')).toHaveClass('truncate')
    expect(screen.queryByText(/\{\{\/badgerdoc\/document\/345/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /remove/i })).not.toBeInTheDocument()
  })

  it('preserves line breaks when llm params contain context chips', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              llm_params: 'Line one {{/badgerdoc/document/345/}}\nLine two',
            },
          })}
        />
      </ol>
    )

    const promptBlock = screen.getByText(/Line one/)
    expect(promptBlock.textContent).toBe('Line one Document\nLine two')
  })

  it('leaves escaped llm params context syntax as plain text', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              llm_params: String.raw`Keep \{{/badgerdoc/document/345/}} as text`,
            },
          })}
        />
      </ol>
    )

    expect(
      screen.getByText(String.raw`Keep \{{/badgerdoc/document/345/}} as text`)
    ).toBeInTheDocument()
    expect(screen.queryByText('Document')).not.toBeInTheDocument()
  })

  it('renders non-string llm params as prompt-like text', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({ workflow_params: { llm_params: { prompt: 'Read' } } })} />
      </ol>
    )

    const promptBlock = screen.getByText(/"prompt": "Read"/)
    expect(promptBlock).toHaveClass('whitespace-pre-wrap')
    expect(promptBlock.closest('pre')).not.toBeInTheDocument()
  })

  it('renders scalar workflow params as compact rows', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              name: 'DeepSeek OCR 2',
              temperature: 0,
              enabled: false,
            },
          })}
        />
      </ol>
    )

    expect(screen.getByText('Workflow details')).toBeInTheDocument()
    expect(screen.getByText('name:')).toBeInTheDocument()
    expect(screen.getByText('DeepSeek OCR 2')).toBeInTheDocument()
    expect(screen.getByText('temperature:')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('enabled:')).toBeInTheDocument()
    expect(screen.getByText('false')).toBeInTheDocument()
    expect(document.querySelector('details')).not.toBeInTheDocument()
  })

  it('renders complex workflow params as collapsible JSON sections', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              options: { retries: 2 },
              items: ['first'],
            },
          })}
        />
      </ol>
    )

    expect(screen.getByText('Workflow details')).toBeInTheDocument()
    const sections = document.querySelectorAll('details')
    expect(sections).toHaveLength(2)
    expect(screen.getByText('options')).toBeInTheDocument()
    expect(screen.getByText(/"retries": 2/)).toBeInTheDocument()
    expect(screen.getByText('items')).toBeInTheDocument()
    expect(screen.getByText(/"first"/)).toBeInTheDocument()
  })

  it('hides empty nested workflow params', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              llm_params: '',
              options: {},
              model: 'DeepSeek OCR 2',
            },
          })}
        />
      </ol>
    )

    expect(screen.queryByText('llm_params')).not.toBeInTheDocument()
    expect(screen.queryByText('options')).not.toBeInTheDocument()
    expect(screen.queryByText('User input')).not.toBeInTheDocument()
    expect(screen.getByText('model:')).toBeInTheDocument()
    expect(screen.getByText('DeepSeek OCR 2')).toBeInTheDocument()
  })

  it('renders numeric task ids', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({ message: 'Task log' }, { task: 42 })} />
      </ol>
    )

    expect(screen.getByText('Task 42')).toBeInTheDocument()
  })

  it('renders compact workflow metadata in the log header', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({
            workflow_params: {
              workflow: {
                name: 'Mineru OCR',
                trigger: 'manual',
                id: 7,
              },
            },
          })}
        />
      </ol>
    )

    expect(screen.getByText('Mineru OCR · manual')).toBeInTheDocument()
    expect(screen.queryByText('id:')).not.toBeInTheDocument()
    expect(screen.getByText('workflow')).toBeInTheDocument()
  })

  it('does not render a source document link for current-document logs', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({ message: 'Current document log' }, { document: 123 })}
          currentDocumentId="123"
        />
      </ol>
    )

    expect(screen.getByText('Current document log')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /document #123/i })).not.toBeInTheDocument()
  })

  it('renders a source document link for child-document logs', () => {
    render(
      <ol>
        <AgentLogEntry
          log={createLog({ message: 'Child document log' }, { document: 456 })}
          currentDocumentId="123"
        />
      </ol>
    )

    const sourceDocumentLink = screen.getByRole('button', { name: /document #456/i })
    expect(sourceDocumentLink).toBeInTheDocument()

    fireEvent.click(sourceDocumentLink)

    expect(mocks.navigate).toHaveBeenCalledWith({
      to: '/documents/$id',
      params: { id: '456' },
      search: { tag: 'agent' },
    })
  })

  it('keeps payload document rendering separate from the source document link', () => {
    mocks.useWorkspaceDocument.mockReturnValue({
      data: {
        id: '456',
        title: 'Payload document',
      },
      isLoading: false,
      isError: false,
    })

    render(
      <ol>
        <AgentLogEntry
          log={createLog({ document: 456 }, { document: 123 })}
          currentDocumentId="123"
        />
      </ol>
    )

    expect(screen.queryByRole('button', { name: /document #456/i })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /payload document/i })).toBeInTheDocument()
  })

  it('styles warning and critical levels distinctly', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({ message: 'Warn' }, { id: 1, level: 'WARNING' })} />
        <AgentLogEntry log={createLog({ message: 'Critical' }, { id: 2, level: 'CRITICAL' })} />
      </ol>
    )

    expect(screen.getByText('WARNING')).toHaveClass('text-amber-600')
    expect(screen.getByText('CRITICAL')).toHaveClass('text-destructive')
  })

  it('renders document payloads and navigates to the referenced document', () => {
    mocks.useWorkspaceDocument.mockReturnValue({
      data: {
        id: '456',
        title: 'Referenced document',
        thumbnailUrl: 'https://example.test/thumb.png',
      },
      isLoading: false,
      isError: false,
    })

    render(
      <ol>
        <AgentLogEntry log={createLog({ document: 456 })} />
      </ol>
    )

    const button = screen.getByRole('button', { name: /referenced document/i })
    expect(within(button).getByText('Document 456')).toBeInTheDocument()

    fireEvent.click(button)

    expect(mocks.navigate).toHaveBeenCalledWith({
      to: '/documents/$id',
      params: { id: '456' },
      search: { tag: 'agent' },
    })
  })
})
