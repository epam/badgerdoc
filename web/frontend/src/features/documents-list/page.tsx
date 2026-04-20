import { useState, useMemo } from 'react'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { FileText, Filter, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useBadgerDocDocuments } from '@/shared/api/hooks/use-badgerdoc-documents'
import { useDuplicateDecisions } from '@/shared/api/hooks/use-duplicate-check'
import type { BadgerDocDocument, DuplicateCheckStatus } from '@/shared/api/badgerdoc/types'
import { useTags } from '@/shared/api/hooks'

/**
 * Extract filename from file URL
 * e.g., http://minio:9000/.../pdf_1.pdf → pdf_1.pdf
 */
function extractFilename(fileUrl: string): string {
  try {
    const url = new URL(fileUrl)
    const segments = url.pathname.split('/')
    return segments[segments.length - 1].split('?')[0] || 'document.pdf'
  } catch {
    return fileUrl || 'document.pdf'
  }
}

/**
 * Format date string to readable format
 */
function formatDate(dateString?: string): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Get effective duplicate status considering localStorage decisions
 */
function getEffectiveDuplicateStatus(
  doc: BadgerDocDocument,
  storedDecisions: Record<string, { status: DuplicateCheckStatus }> | undefined
): { score: number | undefined; status: DuplicateCheckStatus | undefined } {
  const docId = String(doc.id)
  const storedDecision = storedDecisions?.[docId]

  // If there's a stored decision, use that
  if (storedDecision) {
    return {
      score: doc.duplicate_score,
      status: storedDecision.status,
    }
  }

  // Otherwise use the API response
  return {
    score: doc.duplicate_score,
    status: doc.duplicate_status,
  }
}

function DocumentsListSkeleton() {
  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header skeleton */}
      <div>
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-5 w-64 mt-1" />
      </div>

      {/* Filters skeleton */}
      <div className="flex items-center justify-between gap-4">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-10 w-30" />
      </div>

      <div className="divide-y divide-border rounded-xl border border-border">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2">
            <Skeleton className="h-4 w-4" />
            <div className="flex-1">
              <Skeleton className="h-4 w-48" />
              <div className="mt-1 flex gap-2">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <FileText className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold text-foreground">No documents found</h3>
      <p className="text-muted-foreground mt-2">Upload documents to see them listed here.</p>
    </div>
  )
}

interface DocumentRowProps {
  doc: BadgerDocDocument
  onClick: () => void
}

function DocumentRow({ doc, onClick }: DocumentRowProps) {
  const filename = extractFilename(doc.file || doc.file_url || '')

  return (
    <div
      onClick={onClick}
      className="group flex items-center gap-3 px-3 py-2 transition-colors hover:bg-muted/50 cursor-pointer"
    >
      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium text-sm text-foreground">{filename}</span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
          <span>{doc.uploaded_by || 'Unknown'}</span>
          <span>·</span>
          <span>{formatDate(doc.created_at)}</span>
          {doc.tags && doc.tags.length > 0 && (
            <>
              <span>·</span>
              <span>
                {doc.tags.slice(0, 2).join(', ')}
                {doc.tags.length > 2 ? ` + ${doc.tags.length - 2}` : null}
              </span>
            </>
          )}
        </div>
      </div>

      <span className="text-xs font-medium text-primary">View →</span>
    </div>
  )
}

export function DocumentsListPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: '/documents' })
  const [page, setPage] = useState(1)
  const pageSize = 20
  const appliedTagFilterKey = search.tag || null

  const handleTagFilterChange = (tag: string | null) => {
    void navigate({
      to: '/documents',
      search: { tag: tag || undefined },
    })
  }

  const { data, isLoading, error } = useBadgerDocDocuments({
    page,
    page_size: pageSize,
    tags: appliedTagFilterKey || undefined,
  })
  const { data: tags, isLoading: isLoadingTags, error: tagsError } = useTags()
  const appliedTag = tags?.find((t) => t.tag === appliedTagFilterKey)

  // Get stored duplicate decisions
  const { data: storedDecisions } = useDuplicateDecisions()

  const documents = useMemo(() => data?.results || [], [data])
  const totalCount = data?.count || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  // Filter documents: hide confirmed duplicates, apply search
  const filteredDocuments = useMemo(() => {
    const filtered = documents.filter((doc) => {
      const { status } = getEffectiveDuplicateStatus(doc, storedDecisions)

      // Hide confirmed duplicates
      if (status === 'confirmed_duplicate') {
        return false
      }

      return true
    })

    return filtered
  }, [documents, storedDecisions])

  const handleRowClick = (document: BadgerDocDocument) => {
    void navigate({
      to: '/documents/$id',
      params: { id: String(document.id) },
    })
  }

  if (isLoading) {
    return <DocumentsListSkeleton />
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FileText className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold text-foreground">Failed to load documents</h3>
        <p className="text-muted-foreground mt-2">{error?.message ?? 'An error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Documents</h1>
        <p className="text-muted-foreground">All uploaded documents from BadgerDoc</p>
      </div>

      <div className="flex items-center justify-between gap-4">
        <span>
          <span className="mr-2 font-medium text-muted-foreground">Total Documents:</span>
          <span className="font-bold">{totalCount}</span>
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild disabled={isLoadingTags || !!tagsError}>
            <Button variant="outline" size="sm">
              <Filter className="mr-2 h-4 w-4" />
              {appliedTag?.literal || 'All Tags'}
              <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => handleTagFilterChange(null)}>
              All Tags
            </DropdownMenuItem>
            {tags?.map((tag) => (
              <DropdownMenuItem key={tag.tag} onClick={() => handleTagFilterChange(tag.tag)}>
                {tag.literal}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {filteredDocuments.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="divide-y divide-border rounded-xl border border-border">
          {filteredDocuments.map((doc) => (
            <DocumentRow key={doc.id} doc={doc} onClick={() => handleRowClick(doc)} />
          ))}
        </div>
      )}
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, totalCount)} of{' '}
            {totalCount} documents
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
