import { useCallback, useState } from 'react'
import { ChevronDown, Info } from 'lucide-react'
import { DocumentBarPopover, DocumentBarPopoverButton } from '@/components/document-bar-popover'
import {
  DocumentOverviewContent,
  type OverviewDocument,
} from '@/features/workspace/components/document-overview-content'

interface DocumentOverviewPopoverProps {
  document: OverviewDocument
}

export function DocumentOverviewPopover({ document }: DocumentOverviewPopoverProps) {
  const [open, setOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (!nextOpen && isEditing) return

      setOpen(nextOpen)
    },
    [isEditing]
  )

  return (
    <DocumentBarPopover
      open={open}
      onOpenChange={handleOpenChange}
      contentClassName="h-[min(38rem,calc(100vh-8rem))] w-[38rem] overflow-hidden p-0 shadow-lg"
      onInteractOutside={(event) => {
        if (isEditing) event.preventDefault()
      }}
      onEscapeKeyDown={(event) => {
        if (isEditing) event.preventDefault()
      }}
      trigger={({ isOpen }) => (
        <DocumentBarPopoverButton
          isOpen={isOpen}
          className="shrink-0"
          aria-label="Open document overview"
        >
          <Info className="h-4 w-4 shrink-0 text-primary" />
          <span className="text-sm font-medium">Overview</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        </DocumentBarPopoverButton>
      )}
    >
      <DocumentOverviewContent
        key={document.id}
        document={document}
        onEditingChange={setIsEditing}
      />
    </DocumentBarPopover>
  )
}
