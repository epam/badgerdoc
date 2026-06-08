import { ViewerToolbar, type PageChatContext } from '@/components/collection-viewer/viewer-toolbar'
import { useViewerNavigation } from '@/components/collection-viewer/use-viewer-navigation'
import { useOsdViewer } from '@/components/collection-viewer/use-osd-viewer'
import { OverlayBox, PageSource } from '@/shared/api/badgerdoc/types'
import { useDocumentPages } from '@/shared/api/hooks/use-document-workspace'
import { Skeleton } from '@/components/ui/skeleton'
import { useExtractionHighlights } from '@/components/collection-viewer/use-extraction-highlights.ts'
import { useCurrentPageSync } from '@/components/collection-viewer/use-current-page-sync'
import { Dispatch, SetStateAction, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getDocumentExtension } from '@/components/document-hierarchy-utils'
import { cn, extractFilenameFromUrl } from '@/helpers/utils'
import { getApiAdapter } from '@/shared/api/adapters/factory'
import { logger } from '@/shared/logger'
import { toast } from 'sonner'
import { useTouchNavigation } from './use-touch-navigation'

interface CollectionViewerProps {
  documentId: string
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
  pageChatContext?: PageChatContext
}

export function CollectionViewer({
  documentId,
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
  pageChatContext,
}: CollectionViewerProps) {
  const { data: pages, isLoading } = useDocumentPages(documentId)
  const [isDownloading, setIsDownloading] = useState(false)
  const adapter = getApiAdapter()

  // Runtime PNG fallback: when /dzi/ returns URLs but OpenSeadragon fails to
  // actually open the tiled source (broken/missing assets in storage), we
  // fetch PNG renditions and rebuild the viewer with them. Reset whenever the
  // document changes.
  const [runtimeFallbackPages, setRuntimeFallbackPages] = useState<PageSource[] | null>(null)
  const runtimeFallbackRequestedRef = useRef(false)
  useEffect(() => {
    setRuntimeFallbackPages(null)
    runtimeFallbackRequestedRef.current = false
  }, [documentId])

  const handleOsdLoadFailed = useCallback(() => {
    if (runtimeFallbackRequestedRef.current) return
    runtimeFallbackRequestedRef.current = true

    adapter.documents
      .getPngPagesById(documentId)
      .then((sources) => {
        setRuntimeFallbackPages(sources)
      })
      .catch((error) => {
        logger.error('Failed to fetch PNG renditions for OSD fallback', error)
        // Stop retrying for this document; the viewer will stay empty rather
        // than thrash the open-failed event in a loop.
        setRuntimeFallbackPages([])
      })
  }, [adapter.documents, documentId])

  const effectivePages = useMemo(() => runtimeFallbackPages ?? pages, [runtimeFallbackPages, pages])

  const { containerRef, viewer } = useOsdViewer(effectivePages, {
    onLoadFailed: handleOsdLoadFailed,
  })
  // When tiled (DZI) assets are unavailable, the viewer falls back to PNG
  // rendering via OpenSeadragon's simple image source. In that mode the page
  // is read-only: no overlays, no edit mode, no area selection.
  const isPngFallback =
    (effectivePages?.length ?? 0) > 0 && effectivePages!.every((p) => p.type === 'image')
  const effectiveCanUseEditMode = canUseEditMode && !isPngFallback
  const effectiveIsEditMode = isEditMode && !isPngFallback

  const emptyOverlays = useMemo<Record<number, OverlayBox[]>>(() => ({}), [])
  const emptyCreatedIds = useMemo<Set<string>>(() => new Set(), [])

  useExtractionHighlights({
    viewer,
    overlayItems: isPngFallback ? emptyOverlays : highlights,
    selectedHighlightId: isPngFallback ? null : activeHighlightId,
    isEditMode: effectiveIsEditMode,
    createdHighlightIds: isPngFallback ? emptyCreatedIds : createdHighlightIds,
    onHighlightClick,
    onHighlightUpdate,
    onHighlightCreate,
  })
  const { goToPage } = useCurrentPageSync({
    viewer,
    pages: effectivePages || [],
    currentPage,
    setCurrentPage: onPageChange,
  })

  const pagination = useViewerNavigation(effectivePages?.length || 0, currentPage, goToPage)

  useTouchNavigation(viewer)

  const handleZoomIn = useCallback(() => {
    if (!viewer) {
      return
    }

    viewer.viewport.zoomBy(1.2)
    viewer.viewport.applyConstraints()
  }, [viewer])

  const handleZoomOut = useCallback(() => {
    if (!viewer) {
      return
    }

    viewer.viewport.zoomBy(1 / 1.2)
    viewer.viewport.applyConstraints()
  }, [viewer])

  const handleDownloadOriginal = useCallback(async () => {
    if (!documentId || isDownloading) {
      return
    }

    setIsDownloading(true)
    try {
      const documentData = await adapter.documents.getById(documentId)
      const fileUrl = documentData.pdfUrl

      if (!fileUrl) {
        throw new Error('Missing file URL')
      }

      const baseName = documentData.title || extractFilenameFromUrl(fileUrl) || 'document'
      const extension = getDocumentExtension(documentData, baseName)
      const filename =
        extension && !baseName.toLowerCase().endsWith(`.${extension.toLowerCase()}`)
          ? `${baseName}.${extension.toLowerCase()}`
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
  }, [adapter.documents, documentId, isDownloading])

  useEffect(
    function toggleViewerPanForEditMode() {
      if (!viewer) return
      // OSD types don't expose panHorizontal/panVertical on Viewer, but they exist at runtime.
      // Disabling pan keeps scroll-to-zoom and pinch-to-zoom working.
      Object.assign(viewer, {
        panHorizontal: !effectiveIsEditMode,
        panVertical: !effectiveIsEditMode,
      })
    },
    [viewer, effectiveIsEditMode]
  )

  return (
    <section className="flex h-full w-full flex-col">
      <ViewerToolbar
        isLoading={isLoading}
        totalPages={pagination.totalPages}
        currentPage={currentPage}
        onNextClick={pagination.handleNextClick}
        onPrevClick={pagination.handlePrevClick}
        onZoomInClick={handleZoomIn}
        onZoomOutClick={handleZoomOut}
        onFitToPage={pagination.handleFitToPage}
        isEditMode={effectiveIsEditMode}
        canUseEditMode={effectiveCanUseEditMode}
        onToggleEditMode={onToggleEditMode}
        onDownloadOriginal={handleDownloadOriginal}
        isDownloading={isDownloading}
        pageChatContext={pageChatContext}
      />
      {isLoading ? (
        <Skeleton className="h-6 w-96" />
      ) : (
        <div
          ref={containerRef}
          className={cn('relative w-full h-full bg-background', {
            'cursor-crosshair': effectiveIsEditMode,
          })}
          role="region"
          aria-label="Document viewer"
        />
      )}
    </section>
  )
}
