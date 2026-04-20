import OpenSeadragon, { Rect, Viewer } from 'openseadragon'
import { OverlayBox } from '@/shared/api/badgerdoc/types'

// Types

export interface NormalizedBBox {
  x: number
  y: number
  width: number
  height: number
}

export type ResizeDirection = 'nw' | 'ne' | 'sw' | 'se'

// Constants

export const MIN_HIGHLIGHT_SIZE = 0.01

// 1 HOCR pixel = 1/1000 of page in normalized coords
export const MIN_VALID_HIGHLIGHT_SIZE = 0.001

export const isHighlightValid = (bbox: { width: number; height: number }) =>
  bbox.width >= MIN_VALID_HIGHLIGHT_SIZE && bbox.height >= MIN_VALID_HIGHLIGHT_SIZE

export const HIGHLIGHT_CLASS =
  'bg-gray-400/30 hover:bg-gray-400/50 box-border cursor-pointer transition-colors border border-transparent ' +
  'data-[selected=true]:bg-blue-300/60 data-[selected=true]:hover:bg-blue-300/75 ' +
  'data-[selected=true]:border-blue-500 data-[selected=true]:shadow-[0_0_0_2px_rgba(59,130,246,0.4)] ' +
  'data-[editing=true]:ring-2 data-[editing=true]:ring-primary/70 ' +
  'data-[created=true]:bg-emerald-400/30 data-[created=true]:hover:bg-emerald-400/50 ' +
  'data-[created=true]:border-emerald-500 ' +
  'data-[created=true]:data-[selected=true]:bg-emerald-300/60 data-[created=true]:data-[selected=true]:hover:bg-emerald-300/75 ' +
  'data-[created=true]:data-[selected=true]:border-emerald-500 data-[created=true]:data-[selected=true]:shadow-[0_0_0_2px_rgba(16,185,129,0.4)] ' +
  'data-[invalid=true]:bg-red-400/30 data-[invalid=true]:hover:bg-red-400/50 ' +
  'data-[invalid=true]:border-red-500 ' +
  'data-[invalid=true]:data-[selected=true]:bg-red-300/60 data-[invalid=true]:data-[selected=true]:hover:bg-red-300/75 ' +
  'data-[invalid=true]:data-[selected=true]:border-red-500 data-[invalid=true]:data-[selected=true]:shadow-[0_0_0_2px_rgba(239,68,68,0.4)]'

const RESIZE_HANDLE_CLASS =
  'absolute h-2.5 w-2.5 rounded-full bg-primary border border-background shadow pointer-events-auto z-10'

export const DRAW_PREVIEW_CLASS =
  'border-2 border-dashed border-blue-500 bg-blue-200/30 pointer-events-none box-border'

// Math helpers

export const clamp = (value: number, min: number, max: number) =>
  Math.max(min, Math.min(max, value))

export const toOverlayBounds = (bbox: NormalizedBBox, pageBounds: Rect) =>
  new OpenSeadragon.Rect(
    pageBounds.x + pageBounds.width * bbox.x,
    pageBounds.y + pageBounds.height * bbox.y,
    pageBounds.width * bbox.width,
    pageBounds.height * bbox.height
  )

// Tiny floor to prevent overlay from collapsing to zero during resize.
// Highlights below MIN_VALID_HIGHLIGHT_SIZE will render as invalid (red).
const RESIZE_MIN_SIZE = 0.0001

export const computeResizedBBox = (
  initial: NormalizedBBox,
  pointer: { x: number; y: number },
  direction: ResizeDirection
): NormalizedBBox => {
  let left = initial.x
  let top = initial.y
  let right = initial.x + initial.width
  let bottom = initial.y + initial.height

  if (direction.includes('w')) left = clamp(pointer.x, 0, right - RESIZE_MIN_SIZE)
  if (direction.includes('e')) right = clamp(pointer.x, left + RESIZE_MIN_SIZE, 1)
  if (direction.includes('n')) top = clamp(pointer.y, 0, bottom - RESIZE_MIN_SIZE)
  if (direction.includes('s')) bottom = clamp(pointer.y, top + RESIZE_MIN_SIZE, 1)

  return { x: left, y: top, width: right - left, height: bottom - top }
}

// Coordinate helpers

export const viewportPointFromEvent = (viewer: Viewer, event: PointerEvent) => {
  const rect = viewer.container.getBoundingClientRect()
  return viewer.viewport.pointFromPixel(
    new OpenSeadragon.Point(event.clientX - rect.left, event.clientY - rect.top)
  )
}

export const getNormalizedPointer = (viewer: Viewer, event: PointerEvent, pageBounds: Rect) => {
  const vp = viewportPointFromEvent(viewer, event)
  return {
    x: (vp.x - pageBounds.x) / pageBounds.width,
    y: (vp.y - pageBounds.y) / pageBounds.height,
  }
}

export const findPageAtViewportPoint = (viewer: Viewer, point: OpenSeadragon.Point) => {
  const count = viewer.world.getItemCount()
  for (let i = 0; i < count; i++) {
    const pageBounds = viewer.world.getItemAt(i).getBounds()
    if (pageBounds.containsPoint(point)) {
      return { pageIndex: i, pageBounds }
    }
  }
  return null
}

// DOM element factories

const RESIZE_HANDLE_POSITIONS: Record<ResizeDirection, string> = {
  nw: 'top-0 left-0 -translate-x-1/2 -translate-y-1/2 cursor-nwse-resize',
  ne: 'top-0 right-0 translate-x-1/2 -translate-y-1/2 cursor-nesw-resize',
  sw: 'bottom-0 left-0 -translate-x-1/2 translate-y-1/2 cursor-nesw-resize',
  se: 'bottom-0 right-0 translate-x-1/2 translate-y-1/2 cursor-nwse-resize',
}

const createResizeHandle = (direction: ResizeDirection) => {
  const handle = document.createElement('div')
  handle.className = `${RESIZE_HANDLE_CLASS} ${RESIZE_HANDLE_POSITIONS[direction]}`
  handle.dataset.direction = direction
  return handle
}

export const createHighlightElement = (
  overlayBox: OverlayBox,
  isSelected: boolean,
  isEditing: boolean,
  isCreated: boolean,
  isInvalid: boolean
): HTMLDivElement => {
  const el = document.createElement('div')
  el.id = overlayBox.id
  el.className = HIGHLIGHT_CLASS
  el.style.width = '100%'
  el.style.height = '100%'
  el.dataset.selected = String(isSelected)
  el.dataset.editing = String(isEditing)
  el.dataset.created = String(isCreated)
  el.dataset.invalid = String(isInvalid)

  if (isEditing) {
    for (const dir of ['nw', 'ne', 'sw', 'se'] as ResizeDirection[]) {
      el.appendChild(createResizeHandle(dir))
    }
  }

  return el
}
