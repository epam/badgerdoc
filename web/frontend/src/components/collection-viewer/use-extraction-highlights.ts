import { useEffect } from 'react'
import OpenSeadragon, { Rect, Viewer } from 'openseadragon'
import { OverlayBox } from '@/shared/api/badgerdoc/types'
import { logger } from '@/shared/logger'
import {
  type NormalizedBBox,
  type ResizeDirection,
  MIN_HIGHLIGHT_SIZE,
  DRAW_PREVIEW_CLASS,
  clamp,
  toOverlayBounds,
  computeResizedBBox,
  viewportPointFromEvent,
  getNormalizedPointer,
  findPageAtViewportPoint,
  createHighlightElement,
  isHighlightValid,
} from '@/components/collection-viewer/highlight-utils'

export interface UseExtractionHighlightsOptions {
  viewer: Viewer | null
  overlayItems: Record<number, OverlayBox[]>
  selectedHighlightId: string | null
  isEditMode: boolean
  createdHighlightIds: Set<string>
  onHighlightClick: (id: string) => void
  onHighlightUpdate: (blockId: string, pageIndex: number, bbox: NormalizedBBox) => void
  onHighlightCreate: (pageIndex: number, bbox: NormalizedBBox) => void
}

function isViewerReadyForOverlays(viewer: Viewer | null): viewer is Viewer {
  if (!viewer) return false

  const maybeDestroyedViewer = viewer as Viewer & {
    element?: unknown
    container?: unknown
    currentOverlays?: unknown
  }

  return (
    !!maybeDestroyedViewer.element &&
    !!maybeDestroyedViewer.container &&
    Array.isArray(maybeDestroyedViewer.currentOverlays)
  )
}

function clearOverlaysIfReady(viewer: Viewer | null) {
  if (!isViewerReadyForOverlays(viewer)) {
    return false
  }

  try {
    viewer.clearOverlays()
    return true
  } catch (error) {
    logger.error('Failed to clear overlays safely', error)
    return false
  }
}

// Creates a MouseTracker that handles click, move, and resize for an editing overlay.
// OSD manages pointer capture and cleanup — call tracker.destroy() to tear down.
function createEditTracker(
  element: HTMLDivElement,
  viewer: Viewer,
  pageBounds: Rect,
  currentBox: NormalizedBBox,
  overlayBoxId: string,
  pageIndex: number,
  onClick: () => void,
  onUpdate: (blockId: string, pageIndex: number, bbox: NormalizedBBox) => void
): OpenSeadragon.MouseTracker {
  const applyBounds = () => viewer.updateOverlay(element, toOverlayBounds(currentBox, pageBounds))

  let mode: 'move' | 'resize' = 'move'
  let direction: ResizeDirection | undefined
  let initialPointer: { x: number; y: number } | null = null
  let initialBox: NormalizedBBox | null = null
  let didChange = false

  return new OpenSeadragon.MouseTracker({
    element,
    clickHandler: onClick,
    pressHandler: (event) => {
      const origEvent = event.originalEvent as PointerEvent
      const target = origEvent.target as HTMLElement
      direction = target.dataset.direction as ResizeDirection | undefined
      mode = direction ? 'resize' : 'move'
      initialPointer = getNormalizedPointer(viewer, origEvent, pageBounds)
      initialBox = { ...currentBox }
      didChange = false
    },
    dragHandler: (event) => {
      if (!initialPointer || !initialBox) return
      const pointer = getNormalizedPointer(viewer, event.originalEvent as PointerEvent, pageBounds)

      if (mode === 'move') {
        currentBox.x = clamp(initialBox.x + pointer.x - initialPointer.x, 0, 1 - initialBox.width)
        currentBox.y = clamp(initialBox.y + pointer.y - initialPointer.y, 0, 1 - initialBox.height)
      } else if (direction) {
        Object.assign(currentBox, computeResizedBBox(initialBox, pointer, direction))
      }

      didChange = true
      applyBounds()
    },
    dragEndHandler: () => {
      if (didChange) onUpdate(overlayBoxId, pageIndex, { ...currentBox })
      initialPointer = null
      initialBox = null
    },
  })
}

// Main hook

export const useExtractionHighlights = ({
  viewer,
  overlayItems,
  selectedHighlightId,
  isEditMode,
  createdHighlightIds,
  onHighlightClick,
  onHighlightUpdate,
  onHighlightCreate,
}: UseExtractionHighlightsOptions) => {
  useEffect(
    function renderOverlays() {
      if (!viewer) return

      let cancelled = false
      const trackers: OpenSeadragon.MouseTracker[] = []

      const destroyTrackers = () => {
        for (const tracker of trackers) tracker.destroy()
        trackers.length = 0
      }

      const addOverlayBoxes = () => {
        if (!isViewerReadyForOverlays(viewer) || cancelled) return
        destroyTrackers()
        if (!clearOverlaysIfReady(viewer)) return

        const pageCount = viewer.world.getItemCount()
        for (let pageIndex = 0; pageIndex < pageCount; pageIndex++) {
          const pageBounds = viewer.world.getItemAt(pageIndex).getBounds()

          for (const overlayBox of overlayItems[pageIndex + 1] ?? []) {
            const isSelected = selectedHighlightId === overlayBox.id
            const isEditing = isEditMode && isSelected
            const isCreated = createdHighlightIds.has(overlayBox.id)
            const isInvalid = !isHighlightValid(overlayBox)
            const element = createHighlightElement(
              overlayBox,
              isSelected,
              isEditing,
              isCreated,
              isInvalid
            )

            const currentBox: NormalizedBBox = {
              x: overlayBox.x,
              y: overlayBox.y,
              width: overlayBox.width,
              height: overlayBox.height,
            }

            const onClick = () => onHighlightClick(overlayBox.id)

            if (isEditing) {
              trackers.push(
                createEditTracker(
                  element,
                  viewer,
                  pageBounds,
                  currentBox,
                  overlayBox.id,
                  pageIndex,
                  onClick,
                  onHighlightUpdate
                )
              )
            } else {
              trackers.push(new OpenSeadragon.MouseTracker({ element, clickHandler: onClick }))
            }

            viewer.addOverlay(element, toOverlayBounds(currentBox, pageBounds))
          }
        }
      }

      viewer.addHandler('open', addOverlayBoxes)
      addOverlayBoxes()

      return () => {
        cancelled = true
        viewer.removeHandler('open', addOverlayBoxes)
        destroyTrackers()
        clearOverlaysIfReady(viewer)
      }
    },
    [
      overlayItems,
      viewer,
      onHighlightClick,
      selectedHighlightId,
      isEditMode,
      onHighlightUpdate,
      createdHighlightIds,
    ]
  )

  useEffect(
    function rubberbandDraw() {
      if (!viewer || !isEditMode) return

      // Raw DOM events on the container are required here because OSD's own
      // internal MouseTracker on the canvas consumes drag events, preventing a
      // second MouseTracker from receiving dragHandler calls on the same element.
      const container = viewer.container

      let drawState: {
        pageIndex: number
        pageBounds: Rect
        startNorm: { x: number; y: number }
        preview: HTMLDivElement
        currentBox: NormalizedBBox
      } | null = null

      const onPointerMove = (e: PointerEvent) => {
        if (!drawState) return
        e.preventDefault()
        const pointer = getNormalizedPointer(viewer, e, drawState.pageBounds)
        const endX = clamp(pointer.x, 0, 1)
        const endY = clamp(pointer.y, 0, 1)

        drawState.currentBox.x = Math.min(drawState.startNorm.x, endX)
        drawState.currentBox.y = Math.min(drawState.startNorm.y, endY)
        drawState.currentBox.width = Math.abs(endX - drawState.startNorm.x)
        drawState.currentBox.height = Math.abs(endY - drawState.startNorm.y)

        viewer.updateOverlay(
          drawState.preview,
          toOverlayBounds(drawState.currentBox, drawState.pageBounds)
        )
      }

      const onPointerUp = () => {
        window.removeEventListener('pointermove', onPointerMove)
        window.removeEventListener('pointerup', onPointerUp)

        if (!drawState) return
        const { pageIndex, currentBox, preview } = drawState
        drawState = null

        try {
          viewer.removeOverlay(preview)
        } catch {
          /* preview may already be gone */
        }

        if (currentBox.width >= MIN_HIGHLIGHT_SIZE && currentBox.height >= MIN_HIGHLIGHT_SIZE) {
          onHighlightCreate(pageIndex, { ...currentBox })
        }
      }

      const onPointerDown = (event: PointerEvent) => {
        if (event.button !== 0) return
        const target = event.target as HTMLElement
        if (target.closest('[data-selected]')) return
        if (target !== container && !target.closest('.openseadragon-canvas')) return

        const startVP = viewportPointFromEvent(viewer, event)
        const hit = findPageAtViewportPoint(viewer, startVP)
        if (!hit) return

        const { pageIndex, pageBounds } = hit
        const startNorm = {
          x: clamp((startVP.x - pageBounds.x) / pageBounds.width, 0, 1),
          y: clamp((startVP.y - pageBounds.y) / pageBounds.height, 0, 1),
        }

        const preview = document.createElement('div')
        preview.className = DRAW_PREVIEW_CLASS
        preview.style.width = '100%'
        preview.style.height = '100%'

        const currentBox: NormalizedBBox = {
          x: startNorm.x,
          y: startNorm.y,
          width: 0,
          height: 0,
        }
        viewer.addOverlay(preview, toOverlayBounds(currentBox, pageBounds))
        drawState = { pageIndex, pageBounds, startNorm, preview, currentBox }

        window.addEventListener('pointermove', onPointerMove)
        window.addEventListener('pointerup', onPointerUp)
      }

      container.addEventListener('pointerdown', onPointerDown)
      return () => {
        container.removeEventListener('pointerdown', onPointerDown)
        window.removeEventListener('pointermove', onPointerMove)
        window.removeEventListener('pointerup', onPointerUp)
      }
    },
    [viewer, isEditMode, onHighlightCreate]
  )
}
