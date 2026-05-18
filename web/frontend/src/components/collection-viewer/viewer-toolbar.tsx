import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import {
  ZoomIn,
  ZoomOut,
  ChevronRight,
  ChevronLeft,
  Pencil,
  Maximize2,
  Download,
  MessageCirclePlus,
  Layers,
} from 'lucide-react'
import type { ReactNode } from 'react'
import {
  NEXT_BTN_ID,
  PREV_BTN_ID,
  ZOOM_IN_BTN_ID,
  ZOOM_OUT_BTN_ID,
} from '@/components/collection-viewer/config'

export interface PageChatContext {
  canAddWholeDocumentToContext?: boolean
  isWholeDocumentInContext?: boolean
  isWholeDocumentContextDisabled?: boolean
  wholeDocumentContextTooltip?: string
  onAddWholeDocumentToContext?: () => void
  canAddCurrentPageToContext?: boolean
  isCurrentPageInContext?: boolean
  isCurrentPageContextDisabled?: boolean
  currentPageContextTooltip?: string
  onAddCurrentPageToContext?: () => void
}

interface ViewerToolbarProps {
  currentPage: number
  totalPages: number
  onNextClick: () => void
  onPrevClick: () => void
  onZoomInClick?: () => void
  onZoomOutClick?: () => void
  onFitToPage: () => void
  isLoading: boolean
  isEditMode: boolean
  canUseEditMode?: boolean
  onToggleEditMode: () => void
  onDownloadOriginal: () => void
  isDownloading: boolean
  pageChatContext?: PageChatContext
}

function ToolbarContextButton({
  tooltip,
  disabled,
  onClick,
  icon,
  children,
}: {
  tooltip: string
  disabled: boolean
  onClick: () => void
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 px-2 text-xs"
            onMouseDown={(event) => event.preventDefault()}
            onClick={onClick}
            disabled={disabled}
          >
            {icon}
            {children}
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">{tooltip}</TooltipContent>
    </Tooltip>
  )
}

export function ViewerToolbar({
  totalPages,
  currentPage,
  onNextClick,
  onPrevClick,
  onZoomInClick,
  onZoomOutClick,
  onFitToPage,
  isLoading,
  isEditMode,
  canUseEditMode = true,
  onToggleEditMode,
  onDownloadOriginal,
  isDownloading,
  pageChatContext,
}: ViewerToolbarProps) {
  const showPagination = totalPages > 1
  const canAddWholeDocumentToContext = pageChatContext?.canAddWholeDocumentToContext ?? false
  const isWholeDocumentInContext = pageChatContext?.isWholeDocumentInContext ?? false
  const isWholeDocumentContextDisabled = pageChatContext?.isWholeDocumentContextDisabled ?? false
  const onAddWholeDocumentToContext = pageChatContext?.onAddWholeDocumentToContext
  const canAddCurrentPageToContext = pageChatContext?.canAddCurrentPageToContext ?? false
  const isCurrentPageInContext = pageChatContext?.isCurrentPageInContext ?? false
  const isCurrentPageContextDisabled = pageChatContext?.isCurrentPageContextDisabled ?? false
  const onAddCurrentPageToContext = pageChatContext?.onAddCurrentPageToContext
  const documentContextTooltip =
    pageChatContext?.wholeDocumentContextTooltip ??
    (isWholeDocumentInContext ? 'Add another whole document reference' : 'Add document to context')
  const pageContextTooltip =
    pageChatContext?.currentPageContextTooltip ??
    (isCurrentPageInContext
      ? `Add another Page ${currentPage} reference`
      : `Add Page ${currentPage} to context`)
  const hasContextActions = Boolean(
    (canAddWholeDocumentToContext && onAddWholeDocumentToContext) ||
    (canAddCurrentPageToContext && onAddCurrentPageToContext)
  )

  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border bg-card">
      <div className="flex items-center gap-1">
        {isLoading && <Skeleton className="h-8 w-40" />}
        {!isLoading && (showPagination || hasContextActions) && (
          <>
            {showPagination && (
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
            {hasContextActions && (
              <div
                className={
                  showPagination ? 'ml-2 flex items-center gap-1' : 'flex items-center gap-1'
                }
              >
                {canAddCurrentPageToContext && onAddCurrentPageToContext && (
                  <ToolbarContextButton
                    tooltip={pageContextTooltip}
                    onClick={onAddCurrentPageToContext}
                    disabled={isCurrentPageContextDisabled}
                    icon={<MessageCirclePlus className="h-4 w-4" />}
                  >
                    Add page to context
                  </ToolbarContextButton>
                )}
                {canAddWholeDocumentToContext && onAddWholeDocumentToContext && (
                  <ToolbarContextButton
                    tooltip={documentContextTooltip}
                    onClick={onAddWholeDocumentToContext}
                    disabled={isWholeDocumentContextDisabled}
                    icon={<Layers className="h-4 w-4" />}
                  >
                    Add document to context
                  </ToolbarContextButton>
                )}
              </div>
            )}
          </>
        )}
      </div>
      <div className="w-px h-5 bg-border mx-1" />

      <div className="flex items-center gap-1">
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button
            id={ZOOM_OUT_BTN_ID}
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onZoomOutClick}
            disabled={!onZoomOutClick}
          >
            <ZoomOut className="h-4 w-4 m-auto" />
          </Button>
        )}
        {isLoading ? (
          <Skeleton className="h-8 w-8" />
        ) : (
          <Button
            id={ZOOM_IN_BTN_ID}
            variant="ghost"
            size="icon-sm"
            className="h-8 w-8"
            onClick={onZoomInClick}
            disabled={!onZoomInClick}
          >
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
