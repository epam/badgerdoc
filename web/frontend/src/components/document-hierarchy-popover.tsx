import { useState } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
import { DocumentBarPopover, DocumentBarPopoverButton } from '@/components/document-bar-popover'
import { getDocumentExtension } from '@/components/document-hierarchy-utils'
import { cn } from '@/helpers/utils'
import { DocumentHierarchyViewer } from '@/components/document-hierarchy-viewer'
import type { Document } from '@/shared/types/api'
import {
  type DocumentHierarchyNode,
  getBadgerDocDocumentTitle,
  useBadgerDocDocumentHierarchy,
} from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'

interface DocumentHierarchyPopoverProps {
  currentDocument: Document
  onDocumentSelect: (document: Document, node: DocumentHierarchyNode) => void
}

export function DocumentHierarchyPopover({
  currentDocument,
  onDocumentSelect,
}: DocumentHierarchyPopoverProps) {
  const [open, setOpen] = useState(false)
  const hierarchy = useBadgerDocDocumentHierarchy(open ? currentDocument : null)
  const title = getBadgerDocDocumentTitle(currentDocument)
  const extension = getDocumentExtension(currentDocument, title)
  const isPdf = extension === 'PDF'

  const handleDocumentSelect = (document: Document, node: DocumentHierarchyNode) => {
    if (String(document.id) !== String(currentDocument.id)) {
      onDocumentSelect(document, node)
    }

    setOpen(false)
  }

  return (
    <DocumentBarPopover
      open={open}
      onOpenChange={setOpen}
      contentClassName="max-h-[min(34rem,calc(100vh-8rem))] w-[28rem] overflow-y-auto p-3"
      trigger={({ isOpen }) => (
        <DocumentBarPopoverButton
          isOpen={isOpen}
          className="max-w-[min(28rem,48vw)]"
          aria-label="Open document hierarchy"
        >
          <FileText
            className={cn('h-4 w-4 shrink-0', isPdf ? 'text-destructive' : 'text-primary')}
          />
          <span className="min-w-0 truncate text-sm font-medium">{title}</span>
          <ChevronDown className="ml-auto h-4 w-4 shrink-0 text-muted-foreground" />
        </DocumentBarPopoverButton>
      )}
    >
      <DocumentHierarchyViewer
        tree={hierarchy.tree}
        isLoading={hierarchy.isLoading}
        isError={hierarchy.isError}
        errorMessage={hierarchy.errorMessage ?? 'Related documents could not be loaded.'}
        loadingMessage="Loading hierarchy..."
        onDocumentSelect={handleDocumentSelect}
      />
    </DocumentBarPopover>
  )
}
