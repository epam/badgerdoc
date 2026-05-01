import { useQuery } from '@tanstack/react-query'
import { extractFilenameFromUrl } from '@/helpers/utils'
import { badgerDocService } from '../badgerdoc/service'
import type { BadgerDocDocument } from '../badgerdoc/types'

export interface DocumentHierarchyNode {
  id: number | string
  title: string
  document: BadgerDocDocument
  children?: DocumentHierarchyNode[]
  isCurrent?: boolean
  isLeaf?: boolean
}

interface BuildDocumentHierarchyTreeParams {
  currentDocument: BadgerDocDocument
  parentDocument?: BadgerDocDocument | null
  childDocuments?: BadgerDocDocument[]
}

interface DocumentHierarchyData {
  parentDocument: BadgerDocDocument | null
  childDocuments: BadgerDocDocument[]
  tree: DocumentHierarchyNode[]
  parentError: unknown | null
  childrenError: unknown | null
  errorMessage?: string
}

const documentHierarchyKeys = {
  all: ['badgerdoc-document-hierarchy'] as const,
  document: (documentId: string | number, parentDocumentId?: string | number | null) =>
    [...documentHierarchyKeys.all, documentId, parentDocumentId ?? null] as const,
}

export function getBadgerDocDocumentTitle(document: BadgerDocDocument): string {
  const metadataTitle = document.metadata?.title
  if (typeof metadataTitle === 'string' && metadataTitle.trim()) {
    return metadataTitle
  }

  if (document.name?.trim()) {
    return document.name
  }

  return (
    extractFilenameFromUrl(document.file || document.file_url || '') || `Document ${document.id}`
  )
}

function toHierarchyNode(
  document: BadgerDocDocument,
  options?: Pick<DocumentHierarchyNode, 'children' | 'isCurrent' | 'isLeaf'>
): DocumentHierarchyNode {
  return {
    id: document.id,
    title: getBadgerDocDocumentTitle(document),
    document,
    ...options,
  }
}

export function buildDocumentHierarchyTree({
  currentDocument,
  parentDocument,
  childDocuments = [],
}: BuildDocumentHierarchyTreeParams): DocumentHierarchyNode[] {
  const childNodes = childDocuments.map((document) => toHierarchyNode(document, { isLeaf: true }))
  const currentNode = toHierarchyNode(currentDocument, {
    isCurrent: true,
    isLeaf: childNodes.length === 0,
    children: childNodes,
  })

  if (!parentDocument) {
    return [currentNode]
  }

  return [
    toHierarchyNode(parentDocument, {
      children: [currentNode],
    }),
  ]
}

function getHierarchyErrorMessage(parentError: unknown | null, childrenError: unknown | null) {
  if (parentError && childrenError) {
    return 'Parent and child documents could not be loaded.'
  }

  if (parentError) {
    return 'Parent document could not be loaded.'
  }

  if (childrenError) {
    return 'Child documents could not be loaded.'
  }

  return undefined
}

export function useBadgerDocDocumentHierarchy(currentDocument?: BadgerDocDocument | null) {
  const documentId = currentDocument?.id
  const parentDocumentId = currentDocument?.parent_document_id
  const hasParentDocumentId = parentDocumentId !== undefined && parentDocumentId !== null

  const query = useQuery({
    queryKey: documentHierarchyKeys.document(documentId ?? '', parentDocumentId),
    enabled: !!currentDocument && documentId !== undefined && documentId !== null,
    queryFn: async (): Promise<DocumentHierarchyData> => {
      if (!currentDocument) {
        return {
          parentDocument: null,
          childDocuments: [],
          tree: [],
          parentError: null,
          childrenError: null,
        }
      }

      const [parentResult, childrenResult] = await Promise.allSettled([
        hasParentDocumentId
          ? badgerDocService.getDocument(parentDocumentId)
          : Promise.resolve(null),
        badgerDocService.getDocuments({ parent_document_id: documentId }),
      ])

      const parentDocument = parentResult.status === 'fulfilled' ? parentResult.value : null
      const childDocuments =
        childrenResult.status === 'fulfilled' ? childrenResult.value.results : []
      const parentError = parentResult.status === 'rejected' ? parentResult.reason : null
      const childrenError = childrenResult.status === 'rejected' ? childrenResult.reason : null

      return {
        parentDocument,
        childDocuments,
        tree: buildDocumentHierarchyTree({
          currentDocument,
          parentDocument,
          childDocuments,
        }),
        parentError,
        childrenError,
        errorMessage: getHierarchyErrorMessage(parentError, childrenError),
      }
    },
  })
  const parentError = query.data?.parentError ?? null
  const childrenError = query.data?.childrenError ?? null
  const hasHierarchyError = !!parentError || !!childrenError

  return {
    ...query,
    isError: query.isError || hasHierarchyError,
    error: query.error ?? parentError ?? childrenError,
    parentDocument: query.data?.parentDocument ?? null,
    childDocuments: query.data?.childDocuments ?? [],
    parentError,
    childrenError,
    errorMessage:
      query.error instanceof Error
        ? query.error.message
        : (query.data?.errorMessage ?? getHierarchyErrorMessage(parentError, childrenError)),
    tree:
      query.data?.tree ??
      (currentDocument ? buildDocumentHierarchyTree({ currentDocument, childDocuments: [] }) : []),
  }
}
