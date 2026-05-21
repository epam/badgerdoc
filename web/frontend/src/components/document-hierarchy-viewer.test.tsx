import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { DocumentHierarchyNode } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'
import type { Document } from '@/shared/types/api'
import { getDocumentExtension } from './document-hierarchy-utils'
import { DocumentHierarchyViewer } from './document-hierarchy-viewer'

function createDocument(id: number, title: string, options?: Partial<Document>): Document {
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
    tags: [],
    ...options,
  }
}

function createNode(
  id: number,
  title: string,
  options?: Partial<DocumentHierarchyNode>
): DocumentHierarchyNode {
  const document = createDocument(id, title)

  return {
    id: String(id),
    title,
    document,
    ...options,
  }
}

describe('DocumentHierarchyViewer', () => {
  it('detects extension from the visible title before falling back to API fields', () => {
    expect(
      getDocumentExtension(
        {
          id: '1',
          title: 'Untitled',
          type: 'report',
          status: 'analysis_ready',
          pdfUrl: 'https://example.test/source.pdf',
          pageCount: 1,
          authors: [],
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
          tags: [],
          metadata: { title: '7_page_2.png' },
        },
        '7_page_2.png'
      )
    ).toBe('PNG')

    expect(
      getDocumentExtension({
        id: '2',
        title: 'Untitled',
        extension: 'docx',
        type: 'report',
        status: 'analysis_ready',
        pdfUrl: 'https://example.test/source',
        pageCount: 1,
        authors: [],
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        tags: [],
        metadata: { title: 'Untitled' },
      })
    ).toBe('DOCX')
  })

  it('renders the current document inside the tree with its direct children', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        children: [createNode(3, 'Child document', { isLeaf: true })],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const hierarchy = screen.getByRole('tree', { name: /document hierarchy/i })
    expect(within(hierarchy).getByRole('treeitem', { name: /current document/i })).toHaveAttribute(
      'aria-current',
      'page'
    )
    expect(within(hierarchy).getByRole('treeitem', { name: /child document/i })).toHaveAttribute(
      'aria-level',
      '2'
    )
    expect(within(hierarchy).getByRole('treeitem', { name: /child document/i })).toBeDisabled()
    expect(screen.getByText(/end of related documents/i)).toBeInTheDocument()
  })

  it('renders immediate parent, current document, and direct children in order', () => {
    const tree = [
      createNode(1, 'Parent document', {
        children: [
          createNode(2, 'Current document', {
            isCurrent: true,
            children: [
              createNode(3, 'First child', { isLeaf: true }),
              createNode(4, 'Last child', { isLeaf: true }),
            ],
          }),
        ],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const rows = screen.getAllByRole('treeitem')
    expect(rows.map((row) => row.textContent)).toEqual([
      'Parent documentPDF',
      'Current documentPDF',
      'First childPDF',
      'Last childPDF',
    ])
    expect(rows[0]).toHaveAttribute('aria-level', '1')
    expect(rows[1]).toHaveAttribute('aria-level', '2')
    expect(rows[2]).toHaveAttribute('aria-level', '3')
    expect(rows[3]).toHaveAttribute('aria-level', '3')
  })

  it('renders document tags after the extension badge', () => {
    const tree = [
      createNode(2, '7_page_4.png', {
        isCurrent: true,
        document: createDocument(2, '7_page_4.png', {
          tags: ['rendition', 'reviewed'],
        }),
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const row = screen.getByRole('treeitem', { name: /7_page_4\.png/i })
    expect(row).toHaveTextContent('7_page_4.pngPNGrenditionreviewed')
    expect(screen.getByText('rendition')).toBeInTheDocument()
    expect(screen.getByText('reviewed')).toBeInTheDocument()
    expect(screen.queryByText(/\+\d+/)).not.toBeInTheDocument()
  })

  it('renders object tag labels without showing empty tag values', () => {
    const tree = [
      createNode(2, 'Object tags', {
        isCurrent: true,
        document: createDocument(2, 'Object tags', {
          tags: [
            { literal: 'Deepseek OCR 2', tag: 'deepseek-ocr-2' },
            { tag: 'fallback-tag' },
            { literal: '   ', tag: 'literal-fallback' },
            { literal: '   ', tag: '   ' },
            '',
          ] as unknown as string[],
        }),
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const row = screen.getByRole('treeitem', { name: /object tags/i })
    expect(row).toHaveTextContent('Object tagsPDFDeepseek OCR 2fallback-tag+1')
    expect(row).not.toHaveTextContent('[object Object]')
  })

  it('renders one inline tag without overflow', () => {
    const tree = [
      createNode(2, 'Single tag', {
        isCurrent: true,
        document: createDocument(2, 'Single tag', {
          tags: ['rendition'],
        }),
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const row = screen.getByRole('treeitem', { name: /single tag/i })
    expect(row).toHaveTextContent('Single tagPDFrendition')
    expect(screen.queryByText(/\+\d+/)).not.toBeInTheDocument()
  })

  it('renders only two inline tags and a hidden tag count for overflow', () => {
    const tree = [
      createNode(2, 'Overflow tags', {
        isCurrent: true,
        document: createDocument(2, 'Overflow tags', {
          tags: ['rendition', 'reviewed', 'archived', 'important', 'needs-export'],
        }),
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const row = screen.getByRole('treeitem', { name: /overflow tags/i })
    expect(row).toHaveTextContent('Overflow tagsPDFrenditionreviewed+3')
    expect(screen.getByText('rendition')).toBeInTheDocument()
    expect(screen.getByText('reviewed')).toBeInTheDocument()
    expect(screen.getByText('+3')).toBeInTheDocument()
    expect(row).not.toHaveTextContent('archived')
    expect(row).not.toHaveTextContent('important')
    expect(row).not.toHaveTextContent('needs-export')
  })

  it('does not render tag placeholders for missing, null, or empty tags', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        document: createDocument(2, 'Current document', { tags: null as unknown as string[] }),
        children: [
          createNode(3, 'Empty tags', {
            isLeaf: true,
            document: createDocument(3, 'Empty tags', { tags: [] }),
          }),
          createNode(4, 'Missing tags', {
            isLeaf: true,
            document: createDocument(4, 'Missing tags'),
          }),
        ],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    expect(screen.getByRole('treeitem', { name: /current document/i })).toHaveTextContent(
      'Current documentPDF'
    )
    expect(screen.getByRole('treeitem', { name: /empty tags/i })).toHaveTextContent('Empty tagsPDF')
    expect(screen.getByRole('treeitem', { name: /missing tags/i })).toHaveTextContent(
      'Missing tagsPDF'
    )
  })

  it('calls onDocumentSelect for related documents but not the current document', () => {
    const onDocumentSelect = vi.fn()
    const tree = [
      createNode(1, 'Parent document', {
        children: [
          createNode(2, 'Current document', {
            isCurrent: true,
            children: [createNode(3, 'Child document', { isLeaf: true })],
          }),
        ],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} onDocumentSelect={onDocumentSelect} />)

    fireEvent.click(screen.getByRole('treeitem', { name: /parent document/i }))
    fireEvent.click(screen.getByRole('treeitem', { name: /child document/i }))
    expect(screen.getByRole('treeitem', { name: /current document/i })).toBeDisabled()

    expect(onDocumentSelect).toHaveBeenCalledTimes(2)
    expect(onDocumentSelect.mock.calls[0][0]).toMatchObject({ id: '1' })
    expect(onDocumentSelect.mock.calls[1][0]).toMatchObject({ id: '3' })
  })

  it('does not render grandchildren even if a child node includes nested children', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        children: [
          createNode(3, 'Child document', {
            isLeaf: true,
            children: [createNode(4, 'Grandchild document')],
          }),
        ],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    expect(screen.getByRole('treeitem', { name: /child document/i })).toBeInTheDocument()
    expect(screen.queryByText('Grandchild document')).not.toBeInTheDocument()
  })

  it('does not render expand controls for leaf nodes', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        children: [createNode(3, 'Child document', { isLeaf: true })],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    expect(screen.queryByRole('button', { name: /expand/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /collapse/i })).not.toBeInTheDocument()
    expect(screen.getByRole('treeitem', { name: /child document/i })).not.toHaveAttribute(
      'aria-expanded'
    )
  })

  it('renders loading, error, and empty states', () => {
    const { rerender } = render(<DocumentHierarchyViewer tree={[]} isLoading />)

    expect(screen.getByLabelText(/loading document hierarchy/i)).toBeInTheDocument()

    rerender(<DocumentHierarchyViewer tree={[]} isError errorMessage="Hierarchy failed" />)
    expect(screen.getByRole('alert')).toHaveTextContent('Hierarchy failed')

    rerender(<DocumentHierarchyViewer tree={[]} emptyMessage="Nothing related" />)
    expect(screen.getByText('Nothing related')).toBeInTheDocument()
  })

  it('keeps the fallback tree visible while related documents are loading or fail', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        children: [],
      }),
    ]

    const { rerender } = render(
      <DocumentHierarchyViewer tree={tree} isLoading loadingMessage="Loading hierarchy..." />
    )

    expect(screen.getByRole('treeitem', { name: /current document/i })).toBeInTheDocument()
    expect(screen.getByText(/loading hierarchy/i)).toBeInTheDocument()

    rerender(
      <DocumentHierarchyViewer tree={tree} isError errorMessage="Related documents failed" />
    )

    expect(screen.getByRole('treeitem', { name: /current document/i })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Related documents failed')
  })

  it('renders a single highlighted current node for a document with no parent or children', () => {
    const tree = [
      createNode(2, 'Current document', {
        isCurrent: true,
        isLeaf: true,
        children: [],
      }),
    ]

    render(<DocumentHierarchyViewer tree={tree} />)

    const rows = screen.getAllByRole('treeitem')
    expect(rows).toHaveLength(1)
    expect(rows[0]).toHaveAttribute('aria-current', 'page')
    expect(rows[0]).toBeDisabled()
    expect(screen.getByText('Current document')).toHaveClass('truncate')
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.queryByText(/no related documents/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /expand/i })).not.toBeInTheDocument()
  })
})
