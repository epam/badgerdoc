import { useEffect } from 'react'
import OpenSeadragon from 'openseadragon'

/**
 * Normalises a WheelEvent delta to logical pixels,
 * handling the three possible deltaMode values.
 */
const normalizeDelta = (delta: number, deltaMode: number): number => {
  if (deltaMode === WheelEvent.DOM_DELTA_LINE) return delta * 16
  if (deltaMode === WheelEvent.DOM_DELTA_PAGE) return delta * 400
  return delta
}

const SCROLL_MARGIN_PX = 60

/**
 * Clamps a proposed viewport center so it never leaves the world bounds,
 * with an extra SCROLL_MARGIN_PX of breathing room in all directions.
 * When the viewport is larger than the world in one axis (very zoomed out),
 * the center is pinned to the world center on that axis.
 */
const clampCenter = (
  proposed: OpenSeadragon.Point,
  viewportBounds: OpenSeadragon.Rect,
  worldBounds: OpenSeadragon.Rect,
  viewer: OpenSeadragon.Viewer
): OpenSeadragon.Point => {
  // Convert the fixed pixel margin to viewport coordinates.
  const marginVp = viewer.viewport.deltaPointsFromPixels(
    new OpenSeadragon.Point(SCROLL_MARGIN_PX, SCROLL_MARGIN_PX)
  )

  const halfW = viewportBounds.width / 2
  const halfH = viewportBounds.height / 2

  const minX = worldBounds.x - marginVp.x + halfW
  const maxX = worldBounds.x + worldBounds.width + marginVp.x - halfW
  const minY = worldBounds.y - marginVp.y + halfH
  const maxY = worldBounds.y + worldBounds.height + marginVp.y - halfH

  const cx =
    minX > maxX ? worldBounds.x + worldBounds.width / 2 : Math.min(Math.max(proposed.x, minX), maxX)
  const cy =
    minY > maxY
      ? worldBounds.y + worldBounds.height / 2
      : Math.min(Math.max(proposed.y, minY), maxY)

  return new OpenSeadragon.Point(cx, cy)
}

/**
 * Adds touch scroll / gesture navigation to an OpenSeadragon viewer:
 *
 * Mouse:
 *   - Scroll wheel               → pan vertically through pages
 *   - Shift + scroll             → zoom in / out
 *   - Ctrl / Cmd + scroll        → zoom in / out
 *
 * Touchpad:
 *   - Two-finger swipe           → pan horizontally / vertically
 *   - Pinch (reported by the browser as ctrlKey wheel events) → zoom in / out
 *
 * Pan is clamped to the document bounds so the user cannot scroll into
 * empty space past the first or last page.
 */
export const useTouchNavigation = (viewer: OpenSeadragon.Viewer | null): void => {
  useEffect(() => {
    if (!viewer) return

    const handleCanvasScroll = (event: OpenSeadragon.CanvasScrollEvent) => {
      // Prevent OSD's built-in scroll-to-zoom so we fully own the behaviour.
      event.preventDefaultAction = true

      const wheelEvent = event.originalEvent as WheelEvent

      // ctrlKey is set by the browser for touchpad pinch gestures as well as
      // a physical Ctrl key, so this single check covers both cases.
      const shouldZoom = wheelEvent.ctrlKey || wheelEvent.metaKey || wheelEvent.shiftKey

      if (shouldZoom) {
        const normalizedDelta = normalizeDelta(wheelEvent.deltaY, wheelEvent.deltaMode)
        // Exponential curve: ~100 px per tick → ×1.5 / ×0.667 (~50% zoom step per tick)
        const factor = Math.pow(2, -normalizedDelta / 171)
        // Zoom centred on the cursor position
        const refPoint = viewer.viewport.pointFromPixel(event.position)
        viewer.viewport.zoomBy(factor, refPoint, true)
      } else {
        const dx = normalizeDelta(wheelEvent.deltaX, wheelEvent.deltaMode)
        const dy = normalizeDelta(wheelEvent.deltaY, wheelEvent.deltaMode)
        if (dx === 0 && dy === 0) return

        const rawDelta = viewer.viewport.deltaPointsFromPixels(new OpenSeadragon.Point(dx, dy))
        const currentCenter = viewer.viewport.getCenter()
        const proposed = new OpenSeadragon.Point(
          currentCenter.x + rawDelta.x,
          currentCenter.y + rawDelta.y
        )

        // Clamp to document bounds so panning stops at the document edges.
        const worldBounds = viewer.world.getHomeBounds()
        const viewportBounds = viewer.viewport.getBounds()
        const clamped = clampCenter(proposed, viewportBounds, worldBounds, viewer)

        viewer.viewport.panTo(clamped, true)
      }
    }

    viewer.addHandler('canvas-scroll', handleCanvasScroll)
    return () => {
      viewer.removeHandler('canvas-scroll', handleCanvasScroll)
    }
  }, [viewer])
}
