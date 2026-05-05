// Existing endpoint-based hooks (to be migrated to adapter pattern)
export * from './use-upload'
export * from './use-badgerdoc-documents'
export * from './use-badgerdoc-extraction-pages'

export const extractionPagesKeys = {
  all: ['badgerdoc-extraction-pages'] as const,
  document: (documentId: string) => [...extractionPagesKeys.all, documentId] as const,
  documentWithTags: (documentId: string, tags?: string) =>
    [...extractionPagesKeys.document(documentId), tags] as const,
}

// New adapter-based hooks (workspace)
export { useWorkspaceDocument, useUpdateDocumentMeta } from './use-document-workspace'

// Tasks hooks
export { useTask, useTaskStatuses } from './use-tasks'

// Duplicate check hooks

export { useTags } from './use-tags'
