import { ViewerToolbar } from '@/components/collection-viewer/viewer-toolbar'
import { useViewerNavigation } from '@/components/collection-viewer/use-viewer-navigation'
import { useOsdViewer } from '@/components/collection-viewer/use-osd-viewer'
import { OverlayBox } from '@/shared/api/badgerdoc/types'
import { useDocumentPages } from '@/shared/api/hooks/use-document-workspace'
import { Skeleton } from '@/components/ui/skeleton'
import { useExtractionHighlights } from '@/components/collection-viewer/use-extraction-highlights.ts'
import { useCurrentPageSync } from '@/components/collection-viewer/use-current-page-sync'
import { ViewerProcessingState } from '@/components/collection-viewer/viewer-processing-state'
import { Dispatch, SetStateAction, useCallback, useEffect, useState } from 'react'
import { cn, extractFilenameFromUrl } from '@/helpers/utils'
import { badgerDocService } from '@/shared/api/badgerdoc/service'
import { toast } from 'sonner'

interface CollectionViewerProps {
  documentId: string
  expectedPageCount?: number | null
  currentPage: number
  onPageChange: Dispatch<SetStateAction<number>>
  onHighlightClick: (termId: string) => void
  activeHighlightId: string | null
  highlights: Record<number, OverlayBox[]>
  isEditMode: boolean
  canUseEditMode?: boolean
  onToggleEditMode: () => void
  onHighlightUpdate: (
    blockId: string,
    pageIndex: number,
    bbox: { x: number; y: number; width: number; height: number }
  ) => void
  onHighlightCreate: (
    pageIndex: number,
    bbox: { x: number; y: number; width: number; height: number }
  ) => void
  createdHighlightIds: Set<string>
}

export function CollectionViewer({
  documentId,
  expectedPageCount,
  highlights,
  activeHighlightId,
  onHighlightClick,
  currentPage,
  onPageChange,
  isEditMode,
  canUseEditMode = true,
  onToggleEditMode,
  onHighlightUpdate,
  onHighlightCreate,
  createdHighlightIds,
}: CollectionViewerProps) {
  const {
    data: pages,
    isLoading: isLoading,
    refetch,
  } = useDocumentPages(documentId, expectedPageCount)
  const actualPageCount = pages?.length ?? 0
  const pagesReadyByMetadata =
    expectedPageCount != null && expectedPageCount > 0 && actualPageCount >= expectedPageCount
  const isProcessing = !isLoading && !pagesReadyByMetadata
  const isReady = !isLoading && pagesReadyByMetadata
  const { containerRef, viewer } = useOsdViewer(isReady ? pages : undefined)

  const [isDownloading, setIsDownloading] = useState(false)
  useExtractionHighlights({
    viewer,
    overlayItems: highlights,
    selectedHighlightId: activeHighlightId,
    isEditMode,
    createdHighlightIds,
    onHighlightClick,
    onHighlightUpdate,
    onHighlightCreate,
  })
  const { goToPage } = useCurrentPageSync({
    viewer,
    pages: pages || [],
    currentPage,
    setCurrentPage: onPageChange,
  })

  const pagination = useViewerNavigation(pages?.length || 0, currentPage, goToPage)

  const handleDownloadOriginal = useCallback(async () => {
    if (!documentId || isDownloading) {
      return
    }

    setIsDownloading(true)
    try {
      const documentData = await badgerDocService.getDocument(documentId)
      const fileUrl = documentData.file || documentData.file_url

      if (!fileUrl) {
        throw new Error('Missing file URL')
      }

      const baseName = extractFilenameFromUrl(fileUrl) || 'document'
      const extension = documentData.extension
      const filename =
        extension && !baseName.toLowerCase().endsWith(`.${extension.toLowerCase()}`)
          ? `${baseName}.${extension}`
          : baseName

      const response = await fetch(fileUrl)
      if (!response.ok) {
        throw new Error('Failed to fetch file')
      }

      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = objectUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(objectUrl)
    } catch {
      toast.error('Failed to download original file')
    } finally {
      setIsDownloading(false)
    }
  }, [documentId, isDownloading])

  useEffect(
    function toggleViewerPanForEditMode() {
      if (!viewer) return
      // OSD types don't expose panHorizontal/panVertical on Viewer, but they exist at runtime.
      // Disabling pan keeps scroll-to-zoom and pinch-to-zoom working.
      Object.assign(viewer, { panHorizontal: !isEditMode, panVertical: !isEditMode })
    },
    [viewer, isEditMode]
  )

  if (isProcessing) {
    return (
      <section className="flex h-full w-full flex-col">
        <ViewerProcessingState
          onRefresh={() => refetch()}
          readyPagesCount={actualPageCount}
          expectedPagesCount={expectedPageCount}
        />
      </section>
    )
  }

  return (
    <section className="flex h-full w-full flex-col">
      <ViewerToolbar
        isLoading={isLoading}
        totalPages={pagination.totalPages}
        currentPage={currentPage}
        onNextClick={pagination.handleNextClick}
        onPrevClick={pagination.handlePrevClick}
        onFitToPage={pagination.handleFitToPage}
        isEditMode={isEditMode}
        canUseEditMode={canUseEditMode}
        onToggleEditMode={onToggleEditMode}
        onDownloadOriginal={handleDownloadOriginal}
        isDownloading={isDownloading}
      />
      {isLoading ? (
        <Skeleton className="h-6 w-96" />
      ) : (
        <div
          ref={containerRef}
          className={cn('relative w-full h-full bg-background', {
            'cursor-crosshair': isEditMode,
          })}
          role="region"
          aria-label="Document viewer"
        />
      )}
    </section>
  )
}
