import { useState } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
import { getDocumentExtension } from '@/components/document-hierarchy-utils'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/helpers/utils'
import { DocumentHierarchyViewer } from '@/components/document-hierarchy-viewer'
import type { BadgerDocDocument } from '@/shared/api/badgerdoc/types'
import {
  type DocumentHierarchyNode,
  getBadgerDocDocumentTitle,
  useBadgerDocDocumentHierarchy,
} from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'

interface DocumentHierarchyPopoverProps {
  currentDocument: BadgerDocDocument
  onDocumentSelect: (document: BadgerDocDocument, node: DocumentHierarchyNode) => void
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

  const handleDocumentSelect = (document: BadgerDocDocument, node: DocumentHierarchyNode) => {
    if (String(document.id) !== String(currentDocument.id)) {
      onDocumentSelect(document, node)
    }

    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-9 max-w-[min(28rem,48vw)] justify-start gap-2 rounded-xl border-border/70 bg-background px-3 text-foreground shadow-sm hover:bg-muted/60"
          aria-label="Open document hierarchy"
        >
          <FileText
            className={cn('h-4 w-4 shrink-0', isPdf ? 'text-destructive' : 'text-primary')}
          />
          <span className="min-w-0 truncate text-sm font-medium">{title}</span>
          <ChevronDown className="ml-auto h-4 w-4 shrink-0 text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className="max-h-[min(34rem,calc(100vh-8rem))] w-[28rem] max-w-[calc(100vw-2rem)] overflow-y-auto rounded-xl p-3"
      >
        <DocumentHierarchyViewer
          tree={hierarchy.tree}
          isLoading={hierarchy.isLoading}
          isError={hierarchy.isError}
          errorMessage={hierarchy.errorMessage ?? 'Related documents could not be loaded.'}
          loadingMessage="Loading hierarchy..."
          onDocumentSelect={handleDocumentSelect}
        />
      </PopoverContent>
    </Popover>
  )
}
