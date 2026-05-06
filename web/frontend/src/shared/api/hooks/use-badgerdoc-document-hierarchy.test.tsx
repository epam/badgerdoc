import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { badgerDocService } from '../badgerdoc/service'
import type { BadgerDocDocument, BadgerDocDocumentsResponse } from '../badgerdoc/types'
import {
  buildDocumentHierarchyTree,
  getBadgerDocDocumentTitle,
  useBadgerDocDocumentHierarchy,
} from './use-badgerdoc-document-hierarchy'

vi.mock('../badgerdoc/service', () => ({
  badgerDocService: {
    getDocument: vi.fn(),
    getDocuments: vi.fn(),
  },
}))

const getDocumentMock = vi.mocked(badgerDocService.getDocument)
const getDocumentsMock = vi.mocked(badgerDocService.getDocuments)

function createDocument(
  id: number,
  title: string,
  parentDocumentId?: number | null
): BadgerDocDocument {
  return {
    id,
    parent_document_id: parentDocumentId,
    file: `https://example.test/${id}.pdf`,
    metadata: { title },
  }
}

function createDocumentsResponse(results: BadgerDocDocument[]): BadgerDocDocumentsResponse {
  return {
    count: results.length,
    next: null,
    previous: null,
    results,
  }
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('buildDocumentHierarchyTree', () => {
  it('falls back from metadata title to document name, file name, and document id', () => {
    expect(getBadgerDocDocumentTitle(createDocument(1, 'Metadata title'))).toBe('Metadata title')
    expect(
      getBadgerDocDocumentTitle({
        ...createDocument(2, ''),
        name: 'Named document',
        metadata: {},
      })
    ).toBe('Named document')
    expect(
      getBadgerDocDocumentTitle({
        ...createDocument(3, ''),
        file: 'https://example.test/uploads/source.pdf?token=abc',
        metadata: {},
      })
    ).toBe('source.pdf')
    expect(
      getBadgerDocDocumentTitle({
        ...createDocument(4, ''),
        file: '',
        file_url: '',
        metadata: {},
      })
    ).toBe('Document 4')
  })

  it('returns the current document without parent or children', () => {
    const currentDocument = createDocument(2, 'Current document')

    expect(buildDocumentHierarchyTree({ currentDocument })).toEqual([
      expect.objectContaining({
        id: 2,
        title: 'Current document',
        isCurrent: true,
        isLeaf: true,
        children: [],
      }),
    ])
  })

  it('returns the current document with direct children as leaf nodes', () => {
    const currentDocument = createDocument(2, 'Current document')
    const childDocument = createDocument(3, 'Child document', 2)

    const tree = buildDocumentHierarchyTree({
      currentDocument,
      childDocuments: [childDocument],
    })

    expect(tree).toHaveLength(1)
    expect(tree[0]).toMatchObject({
      id: 2,
      isCurrent: true,
      isLeaf: false,
      children: [
        {
          id: 3,
          title: 'Child document',
          isLeaf: true,
        },
      ],
    })
    expect(tree[0].children?.[0].children).toBeUndefined()
  })

  it('returns the immediate parent with current document nested below it', () => {
    const parentDocument = createDocument(1, 'Parent document')
    const currentDocument = createDocument(2, 'Current document', 1)

    expect(
      buildDocumentHierarchyTree({
        parentDocument,
        currentDocument,
      })
    ).toMatchObject([
      {
        id: 1,
        title: 'Parent document',
        children: [
          {
            id: 2,
            title: 'Current document',
            isCurrent: true,
            isLeaf: true,
            children: [],
          },
        ],
      },
    ])
  })

  it('does not include grandparents or grandchildren passed on document records', () => {
    const parentDocument = createDocument(1, 'Parent document', 99)
    const currentDocument = createDocument(2, 'Current document', 1)
    const childDocument = createDocument(3, 'Child document', 2)

    const tree = buildDocumentHierarchyTree({
      parentDocument,
      currentDocument,
      childDocuments: [childDocument],
    })

    expect(tree).toHaveLength(1)
    expect(tree[0].id).toBe(1)
    expect(tree[0].children).toHaveLength(1)
    expect(tree[0].children?.[0].id).toBe(2)
    expect(tree[0].children?.[0].children).toHaveLength(1)
    expect(tree[0].children?.[0].children?.[0]).toMatchObject({
      id: 3,
      isLeaf: true,
    })
    expect(tree[0].children?.[0].children?.[0].children).toBeUndefined()
  })
})

describe('useBadgerDocDocumentHierarchy', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('does not fetch hierarchy data without a current document', () => {
    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(null), {
      wrapper: createWrapper(),
    })

    expect(result.current.tree).toEqual([])
    expect(result.current.parentDocument).toBeNull()
    expect(result.current.childDocuments).toEqual([])
    expect(getDocumentMock).not.toHaveBeenCalled()
    expect(getDocumentsMock).not.toHaveBeenCalled()
  })

  it('fetches direct children for a current document without a parent', async () => {
    const currentDocument = createDocument(2, 'Current document')
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([]))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(getDocumentMock).not.toHaveBeenCalled()
    expect(getDocumentsMock).toHaveBeenCalledTimes(1)
    expect(getDocumentsMock).toHaveBeenCalledWith({ parent_document_id: 2 })
    expect(result.current.tree[0]).toMatchObject({
      id: 2,
      isCurrent: true,
      isLeaf: true,
      children: [],
    })
  })

  it('fetches direct children and marks them as leaf nodes', async () => {
    const currentDocument = createDocument(2, 'Current document')
    const childDocument = createDocument(3, 'Child document', 2)
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([childDocument]))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.tree[0].children).toEqual([
      expect.objectContaining({
        id: 3,
        isLeaf: true,
      }),
    ])
    expect(result.current.tree[0].children?.[0].children).toBeUndefined()
  })

  it('fetches the immediate parent when current document has parent_document_id', async () => {
    const parentDocument = createDocument(1, 'Parent document')
    const currentDocument = createDocument(2, 'Current document', 1)
    getDocumentMock.mockResolvedValue(parentDocument)
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([]))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(getDocumentMock).toHaveBeenCalledTimes(1)
    expect(getDocumentMock).toHaveBeenCalledWith(1)
    expect(result.current.tree).toMatchObject([
      {
        id: 1,
        children: [
          {
            id: 2,
            isCurrent: true,
            children: [],
          },
        ],
      },
    ])
  })

  it('returns immediate parent, current document, and direct children together', async () => {
    const parentDocument = createDocument(1, 'Parent document')
    const currentDocument = createDocument(2, 'Current document', 1)
    const childDocument = createDocument(3, 'Child document', 2)
    getDocumentMock.mockResolvedValue(parentDocument)
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([childDocument]))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.tree).toMatchObject([
      {
        id: 1,
        children: [
          {
            id: 2,
            isCurrent: true,
            isLeaf: false,
            children: [
              {
                id: 3,
                isLeaf: true,
              },
            ],
          },
        ],
      },
    ])
  })

  it('does not recursively load grandparents or grandchildren', async () => {
    const parentDocument = createDocument(1, 'Parent document', 99)
    const currentDocument = createDocument(2, 'Current document', 1)
    const childDocument = createDocument(3, 'Child document', 2)
    getDocumentMock.mockResolvedValue(parentDocument)
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([childDocument]))

    renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(getDocumentsMock).toHaveBeenCalledTimes(1))

    expect(getDocumentMock).toHaveBeenCalledTimes(1)
    expect(getDocumentMock).toHaveBeenCalledWith(1)
    expect(getDocumentMock).not.toHaveBeenCalledWith(99)
    expect(getDocumentsMock).toHaveBeenCalledWith({ parent_document_id: 2 })
    expect(getDocumentsMock).not.toHaveBeenCalledWith({ parent_document_id: 1 })
    expect(getDocumentsMock).not.toHaveBeenCalledWith({ parent_document_id: 3 })
  })

  it('keeps current document and direct children visible when the parent fetch fails', async () => {
    const currentDocument = createDocument(2, 'Current document', 1)
    const childDocument = createDocument(3, 'Child document', 2)
    getDocumentMock.mockRejectedValue(new Error('Parent missing'))
    getDocumentsMock.mockResolvedValue(createDocumentsResponse([childDocument]))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.isError).toBe(true)
    expect(result.current.parentError).toBeInstanceOf(Error)
    expect(result.current.childrenError).toBeNull()
    expect(result.current.errorMessage).toBe('Parent document could not be loaded.')
    expect(result.current.tree).toMatchObject([
      {
        id: 2,
        isCurrent: true,
        children: [
          {
            id: 3,
            isLeaf: true,
          },
        ],
      },
    ])
  })

  it('keeps parent and current document visible when direct children fail to load', async () => {
    const parentDocument = createDocument(1, 'Parent document')
    const currentDocument = createDocument(2, 'Current document', 1)
    getDocumentMock.mockResolvedValue(parentDocument)
    getDocumentsMock.mockRejectedValue(new Error('Children failed'))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.isError).toBe(true)
    expect(result.current.parentError).toBeNull()
    expect(result.current.childrenError).toBeInstanceOf(Error)
    expect(result.current.errorMessage).toBe('Child documents could not be loaded.')
    expect(result.current.tree).toMatchObject([
      {
        id: 1,
        children: [
          {
            id: 2,
            isCurrent: true,
            children: [],
          },
        ],
      },
    ])
  })

  it('keeps current document visible when both parent and direct children fail to load', async () => {
    const currentDocument = createDocument(2, 'Current document', 1)
    getDocumentMock.mockRejectedValue(new Error('Parent failed'))
    getDocumentsMock.mockRejectedValue(new Error('Children failed'))

    const { result } = renderHook(() => useBadgerDocDocumentHierarchy(currentDocument), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.isError).toBe(true)
    expect(result.current.parentError).toBeInstanceOf(Error)
    expect(result.current.childrenError).toBeInstanceOf(Error)
    expect(result.current.errorMessage).toBe('Parent and child documents could not be loaded.')
    expect(result.current.tree).toMatchObject([
      {
        id: 2,
        isCurrent: true,
        isLeaf: true,
        children: [],
      },
    ])
    expect(getDocumentMock).toHaveBeenCalledTimes(1)
    expect(getDocumentsMock).toHaveBeenCalledTimes(1)
  })
})
