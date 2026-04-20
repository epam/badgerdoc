import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ZoomIn,
  ZoomOut,
  ChevronRight,
  ChevronLeft,
  Pencil,
  Maximize2,
  Download,
} from 'lucide-react'
import {
  NEXT_BTN_ID,
  PREV_BTN_ID,
  ZOOM_IN_BTN_ID,
  ZOOM_OUT_BTN_ID,
} from '@/components/collection-viewer/config'

interface ViewerToolbarProps {
  currentPage: number
  totalPages: number
  onNextClick: () => void
  onPrevClick: () => void
  onFitToPage: () => void
  isLoading: boolean
  isEditMode: boolean
  canUseEditMode?: boolean
  onToggleEditMode: () => void
  onDownloadOriginal: () => void
  isDownloading: boolean
}

export function ViewerToolbar({
  totalPages,
  currentPage,
  onNextClick,
  onPrevClick,
  onFitToPage,
  isLoading,
  isEditMode,
  canUseEditMode = true,
  onToggleEditMode,
  onDownloadOriginal,
  isDownloading,
}: ViewerToolbarProps) {
  const showPagination = totalPages > 1

  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border bg-card">
      <div className="flex items-center gap-1">
        {isLoading && <Skeleton className="h-8 w-40" />}
        {!isLoading && showPagination && (
          <>
            <Button
              id={PREV_BTN_ID}
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onPrevClick}
            >
              <ChevronLeft className="h-4 w-4 m-auto" />
            </Button>
            <span className="text-sm tabular-nums min-w-20 text-center">
              <>
                <span className="font-medium">{currentPage}</span>
                <span className="text-muted-foreground"> / {totalPages}</span>
              </>
            </span>
            <Button
              id={NEXT_BTN_ID}
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onNextClick}
            >
              <ChevronRight className="h-4 w-4 m-auto" />
            </Button>
          </>
        )}
      </div>
      <div className="w-px h-5 bg-border mx-1" />

      <div className="flex items-center gap-1">
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button id={ZOOM_OUT_BTN_ID} variant="ghost" size="icon" className="h-8 w-8">
            <ZoomOut className="h-4 w-4 m-auto" />
          </Button>
        )}
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button id={ZOOM_IN_BTN_ID} variant="ghost" size="icon-sm" className="h-8 w-8">
            <ZoomIn className="h-4 w-4 m-auto" />
          </Button>
        )}
        {isLoading && <Skeleton className="h-8 w-8" />}
        {!isLoading && canUseEditMode && (
          <Button
            variant={isEditMode ? 'default' : 'ghost'}
            size="icon"
            className="h-8 w-8"
            onClick={onToggleEditMode}
            aria-pressed={isEditMode}
            aria-label="Toggle drawing mode"
            title="Toggle drawing mode"
          >
            <Pencil className="h-4 w-4 m-auto" />
          </Button>
        )}
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            title="Download original file"
            onClick={onDownloadOriginal}
            disabled={isDownloading}
          >
            <Download className="h-4 w-4 m-auto" />
          </Button>
        )}
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            title="Fit to page"
            onClick={onFitToPage}
          >
            <Maximize2 className="h-4 w-4 m-auto" />
          </Button>
        )}
      </div>
    </div>
  )
}
