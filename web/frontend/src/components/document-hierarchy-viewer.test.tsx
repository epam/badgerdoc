import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { BadgerDocDocument } from '@/shared/api/badgerdoc/types'
import type { DocumentHierarchyNode } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'
import { getDocumentExtension } from './document-hierarchy-utils'
import { DocumentHierarchyViewer } from './document-hierarchy-viewer'

function createDocument(id: number, title: string): BadgerDocDocument {
  return {
    id,
    file: `https://example.test/${id}.pdf`,
    metadata: { title },
  }
}

function createNode(
  id: number,
  title: string,
  options?: Partial<DocumentHierarchyNode>
): DocumentHierarchyNode {
  const document = createDocument(id, title)

  return {
    id,
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
          id: 1,
          extension: 'pdf',
          file: 'https://example.test/source.pdf',
          metadata: { title: '7_page_2.png' },
        },
        '7_page_2.png'
      )
    ).toBe('PNG')

    expect(
      getDocumentExtension({
        id: 2,
        extension: 'docx',
        file: 'https://example.test/source',
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
    expect(onDocumentSelect.mock.calls[0][0]).toMatchObject({ id: 1 })
    expect(onDocumentSelect.mock.calls[1][0]).toMatchObject({ id: 3 })
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
