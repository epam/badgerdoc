import { type ReactNode, type TouchEvent, useState, useRef, useCallback, useEffect } from 'react'
import { cn } from '@/helpers/utils'
import { useUIStore } from '@/shared/hooks/use-ui-store'

interface SplitViewProps {
  left: ReactNode
  right: ReactNode
  defaultRatio?: number
  minRatio?: number
  maxRatio?: number
  persistRatio?: boolean
  className?: string
}

export function SplitView({
  left,
  right,
  defaultRatio = 0.5,
  minRatio = 0.2,
  maxRatio = 0.8,
  persistRatio = true,
  className,
}: SplitViewProps) {
  const storedRatio = useUIStore((s) => s.splitViewRatio)
  const setSplitViewRatio = useUIStore((s) => s.setSplitViewRatio)

  const initialRatio = persistRatio ? storedRatio : defaultRatio
  const [ratio, setRatio] = useState(initialRatio)

  const containerRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)

  const startDragging = useCallback(() => {
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const handleMouseDown = useCallback(() => {
    startDragging()
  }, [startDragging])

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      e.preventDefault()
      startDragging()
    },
    [startDragging]
  )

  const updateRatio = useCallback(
    (clientX: number) => {
      if (!isDragging.current || !containerRef.current) return

      const rect = containerRef.current.getBoundingClientRect()
      const newRatio = (clientX - rect.left) / rect.width

      const clampedRatio = Math.min(maxRatio, Math.max(minRatio, newRatio))
      setRatio(clampedRatio)
    },
    [minRatio, maxRatio]
  )

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      updateRatio(e.clientX)
    },
    [updateRatio]
  )

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (e.touches.length > 0) {
        updateRatio(e.touches[0].clientX)
      }
    },
    [updateRatio]
  ) as unknown as EventListener

  const stopDragging = useCallback(() => {
    if (isDragging.current && persistRatio) {
      // Save to store when drag ends
      setSplitViewRatio(ratio)
    }
    isDragging.current = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [persistRatio, ratio, setSplitViewRatio])

  const handleMouseUp = useCallback(() => {
    stopDragging()
  }, [stopDragging])

  const handleTouchEnd = useCallback(() => {
    stopDragging()
  }, [stopDragging])

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.addEventListener('touchmove', handleTouchMove, { passive: false })
    document.addEventListener('touchend', handleTouchEnd)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', handleTouchEnd)
    }
  }, [handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd])

  // Divider width in pixels - must match the w-1 class (4px)
  const dividerWidth = 4

  return (
    <div ref={containerRef} className={cn('flex h-full w-full overflow-hidden', className)}>
      <div
        className="h-full min-w-0 overflow-hidden"
        style={{ width: `calc(${ratio * 100}% - ${dividerWidth / 2}px)` }}
      >
        {left}
      </div>

      <div
        className="group relative h-full w-1 shrink-0 cursor-col-resize bg-border transition-colors hover:bg-primary touch-none"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Larger touch target for mobile - 16px instead of 8px */}
        <div className="absolute inset-y-0 -left-2 -right-2 md:-left-1 md:-right-1" />
        {/* Visual drag handle indicator on mobile */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 md:hidden">
          <div className="flex flex-col gap-0.5">
            <div className="h-1 w-4 rounded-full bg-primary/50" />
            <div className="h-1 w-4 rounded-full bg-primary/50" />
            <div className="h-1 w-4 rounded-full bg-primary/50" />
          </div>
        </div>
      </div>

      <div
        className="h-full min-w-0 overflow-hidden"
        style={{ width: `calc(${(1 - ratio) * 100}% - ${dividerWidth / 2}px)` }}
      >
        {right}
      </div>
    </div>
  )
}
