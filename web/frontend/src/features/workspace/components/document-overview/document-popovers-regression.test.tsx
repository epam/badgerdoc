import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DocumentHierarchyPopover } from '@/components/document-hierarchy-popover'
import type { Tag } from '@/shared/api/badgerdoc/types'
import type { DocumentHierarchyNode } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'
import type { Document } from '@/shared/types/api'
import { DocumentOverviewPopover } from './document-overview-popover'
import type { OverviewDocument } from './document-overview-content'
import { NoExtractionTagsEmptyState } from '../no-extraction-tags-empty-state'
import { WorkspaceTabs } from '../workspace-tabs'

const mocks = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  useHierarchy: vi.fn(),
}))

vi.mock('@/core/auth/hooks', () => ({
  useAuth: () => ({
    user: { username: 'owner' },
  }),
}))

vi.mock('@/shared/api/hooks', () => ({
  useUpdateDocumentMeta: () => ({
    mutateAsync: mocks.mutateAsync,
    isPending: false,
  }),
}))

vi.mock('@/shared/api/hooks/use-badgerdoc-document-hierarchy', () => ({
  getBadgerDocDocumentTitle: (document: Document) =>
    String(document.metadata?.title ?? document.id),
  useBadgerDocDocumentHierarchy: mocks.useHierarchy,
}))

function createDocument(id: number, title: string): Document {
  return {
    id: String(id),
    title,
    type: 'report',
    status: 'analysis_ready',
    pdfUrl: `https://example.test/${id}.pdf`,
    pageCount: 1,
    metadata: { title },
    authors: [],
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    tags: ['ocr'],
  }
}

function createNode(
  document: Document,
  options?: Partial<DocumentHierarchyNode>
): DocumentHierarchyNode {
  return {
    id: document.id,
    title: String(document.metadata?.title ?? document.id),
    document,
    ...options,
  }
}

function createOverviewDocument(): OverviewDocument {
  return {
    id: 'doc-1',
    title: 'Current document',
    type: 'article',
    metadata: {
      type: 'article',
      journal: 'Testing Journal',
      publication_year: '2026',
    },
    tags: ['science', 'review'],
    uploadedBy: 'owner',
    abstract: 'A concise abstract for regression testing.',
    authors: ['Ada Lovelace'],
    publicationDate: '2026-05-13',
  }
}

function mockHierarchy(currentDocument: Document, childDocument: Document) {
  mocks.useHierarchy.mockImplementation(
    (document) =>
      ({
        tree: document
          ? [
              createNode(currentDocument, {
                isCurrent: true,
                children: [createNode(childDocument, { isLeaf: true })],
              }),
            ]
          : [],
        parentDocument: null,
        childDocuments: document ? [childDocument] : [],
        isLoading: false,
        isError: false,
        error: null,
        data: undefined,
      }) as unknown as ReturnType<
        typeof import('@/shared/api/hooks/use-badgerdoc-document-hierarchy').useBadgerDocDocumentHierarchy
      >
  )
}

describe('document bar popover regression checks', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('keeps Overview data editable and prevents outside-click close while editing', async () => {
    mocks.mutateAsync.mockResolvedValue({ id: 'doc-1' })
    render(<DocumentOverviewPopover document={createOverviewDocument()} />)

    fireEvent.click(screen.getByRole('button', { name: /open document overview/i }))

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Current document')).toBeInTheDocument()
    expect(screen.getAllByText('Testing Journal').length).toBeGreaterThan(0)

    fireEvent.pointerDown(document.body)

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /open document overview/i }))
    fireEvent.click(await screen.findByRole('button', { name: /edit document overview/i }))

    fireEvent.change(screen.getByPlaceholderText(/comma-separated list of tags/i), {
      target: { value: 'updated, regression' },
    })
    fireEvent.change(screen.getByPlaceholderText(/json string/i), {
      target: { value: '{"type":"article","journal":"Updated Journal"}' },
    })

    fireEvent.pointerDown(document.body)

    expect(screen.getByRole('dialog')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(mocks.mutateAsync).toHaveBeenCalledWith({
        id: 'doc-1',
        tags: ['updated', 'regression'],
        metadata: '{"type":"article","journal":"Updated Journal"}',
      })
    )
  })

  it('closes the first document bar popover when the other trigger opens', async () => {
    const currentDocument = createDocument(2, 'Current document')
    const childDocument = createDocument(3, 'Child document')
    mockHierarchy(currentDocument, childDocument)

    render(
      <div>
        <DocumentHierarchyPopover currentDocument={currentDocument} onDocumentSelect={vi.fn()} />
        <DocumentOverviewPopover document={createOverviewDocument()} />
      </div>
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    expect(await screen.findByRole('tree', { name: /document hierarchy/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /open document overview/i }))

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.queryByRole('tree', { name: /document hierarchy/i })).not.toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    expect(await screen.findByRole('tree', { name: /document hierarchy/i })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText('Testing Journal')).not.toBeInTheDocument())
  })

  it('renders Agent alongside extraction tabs and keeps Overview out', () => {
    const extractionTags: Tag[] = [
      { tag: 'deepseek-ocr-2', literal: 'Deepseek OCR 2', order: 1 },
      { tag: 'mineru-ocr', literal: 'Mineru OCR', order: 2 },
      { tag: 'paddle-ocr', literal: 'Paddle OCR', order: 3 },
    ]

    render(
      <WorkspaceTabs
        activeTab="agent"
        onTabChange={vi.fn()}
        extractionTags={extractionTags}
      />
    )

    expect(screen.queryByRole('tab', { name: /overview/i })).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /agent/i })).toHaveAttribute(
      'aria-selected',
      'true'
    )
    expect(screen.getByRole('tab', { name: /deepseek ocr 2/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /mineru ocr/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /paddle ocr/i })).toBeInTheDocument()
  })

  it('keeps Agent available when there are no extraction tags', () => {
    render(
      <WorkspaceTabs
        activeTab="agent"
        onTabChange={vi.fn()}
        extractionTags={[]}
        isLoadingTags={false}
      />
    )

    expect(screen.getByRole('tablist')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /agent/i })).toHaveAttribute('aria-selected', 'true')

    render(<NoExtractionTagsEmptyState />)

    expect(
      screen.getByRole('heading', { name: /no extraction results available/i })
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/no extraction data found for "extraction results"/i)
    ).not.toBeInTheDocument()
  })
})
