import { AlertCircle, Check, FileText } from 'lucide-react'
import { cn } from '@/helpers/utils'
import { getDocumentExtension } from '@/components/document-hierarchy-utils'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Spinner } from '@/components/ui/spinner'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Document } from '@/shared/types/api'
import type { DocumentHierarchyNode } from '@/shared/api/hooks/use-badgerdoc-document-hierarchy'

interface DocumentHierarchyViewerProps {
  tree: DocumentHierarchyNode[]
  isLoading?: boolean
  isError?: boolean
  errorMessage?: string
  loadingMessage?: string
  emptyMessage?: string
  className?: string
  onDocumentSelect?: (document: Document, node: DocumentHierarchyNode) => void
}

interface DocumentHierarchyRowProps {
  node: DocumentHierarchyNode
  level: number
  isLast: boolean
  onDocumentSelect?: (document: Document, node: DocumentHierarchyNode) => void
}

interface VisibleHierarchyRow {
  node: DocumentHierarchyNode
  level: number
  isLast: boolean
}

const MAX_INLINE_TAGS = 2

function getVisibleHierarchyRows(tree: DocumentHierarchyNode[]): VisibleHierarchyRow[] {
  const rootNode = tree[0]
  if (!rootNode) return []

  const currentNode = rootNode.isCurrent
    ? rootNode
    : rootNode.children?.find((node) => node.isCurrent)
  const currentLevel = rootNode.isCurrent ? 0 : 1
  const rows: VisibleHierarchyRow[] = [
    {
      node: rootNode,
      level: 0,
      isLast: true,
    },
  ]

  if (currentNode && currentNode.id !== rootNode.id) {
    rows.push({
      node: currentNode,
      level: currentLevel,
      isLast: currentNode.children?.length ? false : true,
    })
  }

  const childDocuments = currentNode?.children ?? []
  childDocuments.forEach((node, index) => {
    rows.push({
      node: { ...node, isLeaf: true },
      level: currentLevel + 1,
      isLast: index === childDocuments.length - 1,
    })
  })

  return rows
}

function DocumentHierarchyLoadingState() {
  return (
    <div className="space-y-1.5" aria-label="Loading document hierarchy">
      <div className="flex items-center gap-2 rounded-md bg-muted/60 px-2 py-1.5 text-xs text-muted-foreground">
        <Spinner size="sm" className="h-3.5 w-3.5" />
        <span>Loading related documents...</span>
      </div>
      <Skeleton variant="text" className="h-7 w-full" />
      <Skeleton variant="text" className="ml-4 h-7 w-[82%]" />
    </div>
  )
}

function DocumentHierarchyConnector({ level, isLast }: { level: number; isLast: boolean }) {
  if (level === 0) return null

  const connectorLeft = level * 18 - 8

  return (
    <span aria-hidden="true" className="pointer-events-none absolute inset-y-0">
      <span
        className={cn('absolute top-0 w-px bg-border', isLast ? 'h-1/2' : 'h-full')}
        style={{ left: `${connectorLeft}px` }}
      />
      <span
        className="absolute top-1/2 h-px w-3.5 bg-border"
        style={{ left: `${connectorLeft}px` }}
      />
    </span>
  )
}

function getDocumentTagLabel(tag: unknown): string {
  if (typeof tag === 'string') {
    return tag.trim()
  }

  if (tag && typeof tag === 'object') {
    const tagRecord = tag as Record<string, unknown>
    const labels = [tagRecord.literal, tagRecord.tag]

    for (const label of labels) {
      if (typeof label === 'string' && label.trim()) {
        return label.trim()
      }
    }
  }

  return ''
}

export function DocumentHierarchyRow({
  node,
  level,
  isLast,
  onDocumentSelect,
}: DocumentHierarchyRowProps) {
  const isCurrent = !!node.isCurrent
  const canNavigate = !isCurrent && !!onDocumentSelect
  const extension = getDocumentExtension(node.document, node.title)
  const isPdf = extension === 'PDF'
  const documentTags = Array.isArray(node.document.tags)
    ? node.document.tags.map(getDocumentTagLabel).filter(Boolean)
    : []
  const visibleTags = documentTags.slice(0, MAX_INLINE_TAGS)
  const hiddenTags = documentTags.slice(MAX_INLINE_TAGS)

  return (
    <div className="relative py-1" role="none">
      <DocumentHierarchyConnector level={level} isLast={isLast} />
      <button
        type="button"
        role="treeitem"
        aria-current={isCurrent ? 'page' : undefined}
        aria-level={level + 1}
        disabled={!canNavigate}
        onClick={canNavigate ? () => onDocumentSelect(node.document, node) : undefined}
        className={cn(
          'group relative z-10 flex h-9 w-full min-w-0 items-center gap-2 rounded-lg border border-transparent py-1.5 pr-2.5 text-left text-sm outline-none transition-colors',
          'focus-visible:bg-muted focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-1 focus-visible:ring-offset-card',
          canNavigate && 'cursor-pointer hover:border-border/70 hover:bg-muted/70',
          isCurrent &&
            'border-primary/15 bg-primary/10 font-medium text-foreground shadow-sm ring-1 ring-primary/15 hover:bg-primary/15 focus-visible:bg-primary/15 focus-visible:ring-primary/40',
          !canNavigate && !isCurrent && 'cursor-default text-foreground'
        )}
        style={{ paddingLeft: `${level * 18 + 8}px` }}
      >
        <FileText
          className={cn('h-4 w-4 shrink-0', isPdf ? 'text-destructive' : 'text-primary')}
          aria-hidden="true"
        />
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="min-w-0 flex-1 truncate">{node.title}</span>
          </TooltipTrigger>
          <TooltipContent side="bottom" align="start" className="max-w-80">
            {node.title}
          </TooltipContent>
        </Tooltip>
        {(extension || documentTags.length > 0) && (
          <span className="flex min-w-0 max-w-[60%] shrink-0 items-center gap-1.5 overflow-hidden">
            {extension && (
              <span className="inline-flex h-5 shrink-0 items-center rounded-full bg-muted px-1.5 text-[10px] font-semibold leading-none text-muted-foreground ring-1 ring-border/60">
                {extension}
              </span>
            )}
            {extension && documentTags.length > 0 && (
              <span aria-hidden="true" className="h-4 w-px shrink-0 bg-border/70" />
            )}
            {documentTags.length > 0 && (
              <span className="flex min-w-0 flex-1 items-center gap-1 overflow-hidden">
                {visibleTags.map((tag, index) => (
                  <Badge
                    key={`${tag}-${index}`}
                    variant="info"
                    className="h-5 max-w-24 shrink justify-start overflow-hidden text-ellipsis rounded-full px-1.5 py-0 text-[11px] leading-none"
                  >
                    {tag}
                  </Badge>
                ))}
                {hiddenTags.length > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge
                        variant="info"
                        className="h-5 rounded-full px-1.5 py-0 text-[11px] leading-none"
                      >
                        +{hiddenTags.length}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" align="end" className="max-w-64 break-words">
                      {hiddenTags.join(', ')}
                    </TooltipContent>
                  </Tooltip>
                )}
              </span>
            )}
          </span>
        )}
        {isCurrent && <Check className="ml-1 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />}
      </button>
    </div>
  )
}

export function DocumentHierarchyViewer({
  tree,
  isLoading = false,
  isError = false,
  errorMessage = 'Failed to load document hierarchy.',
  loadingMessage = 'Loading related documents...',
  emptyMessage = 'No related documents.',
  className,
  onDocumentSelect,
}: DocumentHierarchyViewerProps) {
  const rows = getVisibleHierarchyRows(tree)

  if (isLoading && rows.length === 0) {
    return (
      <div className={cn('w-full min-w-0', className)}>
        <DocumentHierarchyLoadingState />
      </div>
    )
  }

  if (isError && rows.length === 0) {
    return (
      <div
        className={cn(
          'flex min-w-0 items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive',
          className
        )}
        role="alert"
      >
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="min-w-0">{errorMessage}</span>
      </div>
    )
  }

  if (rows.length === 0) {
    return <div className={cn('p-3 text-sm text-muted-foreground', className)}>{emptyMessage}</div>
  }

  return (
    <div className={cn('w-full min-w-0', className)}>
      <div
        role="tree"
        aria-label="Document hierarchy"
        className="relative rounded-lg border border-border/70 bg-background p-2"
      >
        {rows.map(({ node, level, isLast }) => (
          <DocumentHierarchyRow
            key={`${level}-${node.id}`}
            node={node}
            level={level}
            isLast={isLast}
            onDocumentSelect={onDocumentSelect}
          />
        ))}
      </div>
      {isLoading && (
        <div className="mt-2 flex items-center gap-2 rounded-md bg-muted/60 px-2 py-1.5 text-xs text-muted-foreground">
          <Spinner size="sm" className="h-3.5 w-3.5" />
          <span>{loadingMessage}</span>
        </div>
      )}
      {isError && (
        <div
          className="mt-2 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-2 py-1.5 text-xs text-destructive"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>{errorMessage}</span>
        </div>
      )}
      <div className="mt-2 border-t border-border/60 pt-2 text-xs text-muted-foreground">
        End of related documents
      </div>
    </div>
  )
}
