import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { BadgerDocDocument } from '@/shared/api/badgerdoc/types'
import type { DocumentHierarchyNode } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'
import { useBadgerDocDocumentHierarchy } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'
import { DocumentHierarchyPopover } from './document-hierarchy-popover'

vi.mock('@/shared/api/hooks/use-badgerdoc-document-hierarchy', () => ({
  getBadgerDocDocumentTitle: (document: BadgerDocDocument) =>
    String(document.metadata?.title ?? document.id),
  useBadgerDocDocumentHierarchy: vi.fn(),
}))

const useHierarchyMock = vi.mocked(useBadgerDocDocumentHierarchy)

function createDocument(id: number, title: string): BadgerDocDocument {
  return {
    id,
    file: `https://example.test/${id}.pdf`,
    metadata: { title },
  }
}

function createNode(
  document: BadgerDocDocument,
  options?: Partial<DocumentHierarchyNode>
): DocumentHierarchyNode {
  return {
    id: document.id,
    title: String(document.metadata?.title ?? document.id),
    document,
    ...options,
  }
}

describe('DocumentHierarchyPopover', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('opens the hierarchy viewer and closes after selecting another document', async () => {
    const currentDocument = createDocument(2, 'Current document')
    const childDocument = createDocument(3, 'Child document')
    const onDocumentSelect = vi.fn()

    useHierarchyMock.mockImplementation(
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
        }) as unknown as ReturnType<typeof useBadgerDocDocumentHierarchy>
    )

    render(
      <DocumentHierarchyPopover
        currentDocument={currentDocument}
        onDocumentSelect={onDocumentSelect}
      />
    )

    expect(useHierarchyMock).toHaveBeenLastCalledWith(null)

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    expect(await screen.findByRole('tree', { name: /document hierarchy/i })).toBeInTheDocument()
    expect(useHierarchyMock).toHaveBeenLastCalledWith(currentDocument)

    fireEvent.click(screen.getByRole('treeitem', { name: /child document/i }))

    expect(onDocumentSelect).toHaveBeenCalledTimes(1)
    expect(onDocumentSelect.mock.calls[0][0]).toMatchObject({ id: 3 })
    await waitFor(() =>
      expect(screen.queryByRole('tree', { name: /document hierarchy/i })).not.toBeInTheDocument()
    )
  })

  it('does not navigate when clicking the current document row', async () => {
    const currentDocument = createDocument(2, 'Current document')
    const onDocumentSelect = vi.fn()

    useHierarchyMock.mockImplementation(
      (document) =>
        ({
          tree: document ? [createNode(currentDocument, { isCurrent: true, children: [] })] : [],
          parentDocument: null,
          childDocuments: [],
          isLoading: false,
          isError: false,
          error: null,
          data: undefined,
        }) as unknown as ReturnType<typeof useBadgerDocDocumentHierarchy>
    )

    render(
      <DocumentHierarchyPopover
        currentDocument={currentDocument}
        onDocumentSelect={onDocumentSelect}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))
    fireEvent.click(await screen.findByRole('treeitem', { name: /current document/i }))

    expect(onDocumentSelect).not.toHaveBeenCalled()
    expect(screen.getByRole('tree', { name: /document hierarchy/i })).toBeInTheDocument()
  })

  it('shows loading state inside the open popover', async () => {
    const currentDocument = createDocument(2, 'Current document')

    useHierarchyMock.mockImplementation(
      (document) =>
        ({
          tree: document ? [createNode(currentDocument, { isCurrent: true, children: [] })] : [],
          parentDocument: null,
          childDocuments: [],
          isLoading: !!document,
          isError: false,
          error: null,
          data: undefined,
        }) as unknown as ReturnType<typeof useBadgerDocDocumentHierarchy>
    )

    render(
      <DocumentHierarchyPopover currentDocument={currentDocument} onDocumentSelect={vi.fn()} />
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    expect(await screen.findByText(/loading hierarchy/i)).toBeInTheDocument()
    expect(screen.getByRole('treeitem', { name: /current document/i })).toBeInTheDocument()
  })

  it('shows error state inside the open popover without hiding the current document', async () => {
    const currentDocument = createDocument(2, 'Current document')

    useHierarchyMock.mockImplementation(
      (document) =>
        ({
          tree: document ? [createNode(currentDocument, { isCurrent: true, children: [] })] : [],
          parentDocument: null,
          childDocuments: [],
          isLoading: false,
          isError: !!document,
          error: new Error('Parent failed'),
          errorMessage: 'Parent document could not be loaded.',
          data: undefined,
        }) as unknown as ReturnType<typeof useBadgerDocDocumentHierarchy>
    )

    render(
      <DocumentHierarchyPopover currentDocument={currentDocument} onDocumentSelect={vi.fn()} />
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    expect(await screen.findByRole('treeitem', { name: /current document/i })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Parent document could not be loaded.')
  })

  it('uses a scrollable popover panel for long hierarchies', async () => {
    const currentDocument = createDocument(2, '7_page_2.png')
    const childDocuments = Array.from({ length: 20 }, (_, index) =>
      createDocument(index + 3, `14_${index}.png`)
    )

    useHierarchyMock.mockImplementation(
      (document) =>
        ({
          tree: document
            ? [
                createNode(currentDocument, {
                  isCurrent: true,
                  children: childDocuments.map((childDocument) =>
                    createNode(childDocument, { isLeaf: true })
                  ),
                }),
              ]
            : [],
          parentDocument: null,
          childDocuments: document ? childDocuments : [],
          isLoading: false,
          isError: false,
          error: null,
          data: undefined,
        }) as unknown as ReturnType<typeof useBadgerDocDocumentHierarchy>
    )

    render(
      <DocumentHierarchyPopover currentDocument={currentDocument} onDocumentSelect={vi.fn()} />
    )

    fireEvent.click(screen.getByRole('button', { name: /open document hierarchy/i }))

    const popoverPanel = await screen.findByRole('dialog')
    expect(popoverPanel).toHaveClass('overflow-y-auto')
    expect(screen.getAllByText('PNG').length).toBeGreaterThan(1)
  })
})
