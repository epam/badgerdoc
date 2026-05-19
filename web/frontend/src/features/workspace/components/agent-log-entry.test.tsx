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
    expect(labels).toEqual(['Message', 'Markdown', 'Code', 'Workflow Params'])
    expect(screen.getByText('Plain message')).toBeInTheDocument()
    expect(screen.getAllByText('Markdown').find((node) => node.tagName === 'STRONG')).toHaveClass(
      'font-semibold'
    )
    expect(screen.getByText(/const ok = true/)).toBeInTheDocument()
    expect(screen.getByText(/"model": "test"/)).toBeInTheDocument()
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

  it.each([
    ['object', { model: 'test' }, '"model": "test"'],
    ['array', ['item'], '"item"'],
    ['false boolean', false, 'false'],
    ['zero number', 0, '0'],
    ['non-empty string', 'value', '"value"'],
  ])('renders meaningful workflow params when value is %s', (_label, workflowParams, expected) => {
    const { container } = render(
      <ol>
        <AgentLogEntry log={createLog({ workflow_params: workflowParams })} />
      </ol>
    )

    expect(screen.getByText(/workflow params/i)).toBeInTheDocument()
    expect(container.querySelector('pre code')).toHaveTextContent(expected)
  })

  it('renders numeric task ids', () => {
    render(
      <ol>
        <AgentLogEntry log={createLog({ message: 'Task log' }, { task: 42 })} />
      </ol>
    )

    expect(screen.getByText('Task 42')).toBeInTheDocument()
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
