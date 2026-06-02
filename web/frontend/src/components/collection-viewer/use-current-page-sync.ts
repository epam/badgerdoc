import { useEffect, useRef, useCallback } from 'react'
import OpenSeadragon from 'openseadragon'
import type { PageSource } from '@/shared/api/badgerdoc/types'

interface UseCurrentPageSyncParams {
  viewer: OpenSeadragon.Viewer | null
  pages: PageSource[]
  currentPage: number
  setCurrentPage: (page: number) => void
}

const throttle = (func: () => void, interval: number) => {
  let lastExecuted: number | null = null
  let timeoutId: number | null = null

  return () => {
    const now = Date.now()
    if (lastExecuted && now - lastExecuted < interval) {
      if (timeoutId) clearTimeout(timeoutId)
      timeoutId = window.setTimeout(
        () => {
          lastExecuted = Date.now()
          func()
        },
        interval - (now - lastExecuted)
      )
    } else {
      lastExecuted = now
      func()
    }
  }
}

export function useCurrentPageSync({
  viewer,
  pages,
  currentPage,
  setCurrentPage,
}: UseCurrentPageSyncParams) {
  const isNavigatingRef = useRef(false)
  const lastViewportBoundsRef = useRef<OpenSeadragon.Rect | null>(null)
  const currentPageRef = useRef(currentPage)

  useEffect(() => {
    currentPageRef.current = currentPage
  }, [currentPage])

  const getPageBounds = useCallback(
    (pageNumber: number) => {
      if (!viewer) return new OpenSeadragon.Rect(0, 0, 1, 1)
      const tiledImage = viewer.world.getItemAt(pageNumber - 1)
      return tiledImage?.getBounds() ?? new OpenSeadragon.Rect(0, 0, 1, 1)
    },
    [viewer]
  )

  const getIntersectionArea = useCallback((a: OpenSeadragon.Rect, b: OpenSeadragon.Rect) => {
    const xOverlap = Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x))
    const yOverlap = Math.max(0, Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y))
    return xOverlap * yOverlap
  }, [])

  const getCenter = useCallback(
    (rect: OpenSeadragon.Rect) => ({
      x: rect.x + rect.width / 2,
      y: rect.y + rect.height / 2,
    }),
    []
  )

  const getCurrentPageFromViewport = useCallback(() => {
    if (!viewer) return currentPageRef.current
    const viewport = viewer.viewport.getBounds(true)
    const viewportCenter = getCenter(viewport)

    let bestPage = 1
    let bestVisible = -1
    let bestDistance = Infinity

    pages.forEach((_, index) => {
      const page = index + 1
      const bounds = getPageBounds(page)

      const intersection = getIntersectionArea(bounds, viewport)
      const area = bounds.width * bounds.height || 1
      const visible = intersection / area

      const center = getCenter(bounds)
      const distance = Math.hypot(center.x - viewportCenter.x, center.y - viewportCenter.y)

      if (visible > bestVisible || (visible === bestVisible && distance < bestDistance)) {
        bestPage = page
        bestVisible = visible
        bestDistance = distance
      }
    })

    return bestPage
  }, [viewer, pages, getPageBounds, getIntersectionArea, getCenter])

  useEffect(() => {
    if (!viewer) return

    const throttledUpdateCurrentPage = throttle(() => {
      if (!viewer || isNavigatingRef.current) return

      const currentViewportBounds = viewer.viewport.getBounds(true)
      const nextPage = getCurrentPageFromViewport()
      if (nextPage !== currentPageRef.current) {
        setCurrentPage(nextPage)
        lastViewportBoundsRef.current = currentViewportBounds
      }
    }, 200) // 200ms

    viewer.addHandler('viewport-change', throttledUpdateCurrentPage)
    return () => {
      viewer.removeHandler('viewport-change', throttledUpdateCurrentPage)
    }
  }, [viewer, setCurrentPage, getCurrentPageFromViewport])

  const goToPage = useCallback<React.Dispatch<React.SetStateAction<number>>>(
    (value) => {
      if (!viewer) return

      const page = typeof value === 'function' ? value(currentPageRef.current) : value

      isNavigatingRef.current = true
      setCurrentPage(page)

      const bounds = getPageBounds(page)
      viewer.viewport.fitBounds(bounds, true)
      window.requestAnimationFrame(() => {
        isNavigatingRef.current = false
      })
    },
    [viewer, setCurrentPage, getPageBounds]
  )

  useEffect(() => {
    if (!viewer) return

    const onFinish = () => {
      isNavigatingRef.current = false
    }

    viewer.addHandler('animation-finish', onFinish)
    return () => {
      viewer.removeHandler('animation-finish', onFinish)
    }
  }, [viewer])

  // Navigate the viewer when currentPage is changed externally (e.g. from the right panel).
  // When the change comes from viewport scrolling, the viewer already shows the correct page.
  useEffect(() => {
    if (!viewer || isNavigatingRef.current) return
    const viewportPage = getCurrentPageFromViewport()
    if (viewportPage !== currentPage) {
      isNavigatingRef.current = true
      const bounds = getPageBounds(currentPage)
      viewer.viewport.fitBounds(bounds, true)
      window.requestAnimationFrame(() => {
        isNavigatingRef.current = false
      })
    }
  }, [currentPage, viewer, getCurrentPageFromViewport, getPageBounds])

  return { goToPage }
}
