import { useEffect, useRef, useState } from 'react'
import OpenSeadragon, { Options, Viewer as OSDViewer } from 'openseadragon'
import { logger } from '@/shared/logger.ts'
import { DEFAULT_OSD_CONFIG } from '@/components/collection-viewer/config'

export const useOsdViewer = (tileSources?: string[]) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [viewer, setViewer] = useState<OSDViewer | null>(null)

  useEffect(
    function initViewerForDocument() {
      if (!containerRef.current) return

      let cancelled = false

      void (async () => {
        if (viewer) {
          return
        }
        try {
          const viewer = new OpenSeadragon.Viewer({
            element: containerRef.current!,
            ...DEFAULT_OSD_CONFIG,
            tileSources,
          } as Partial<Options>)
          setViewer(viewer)

          if (cancelled) return

          viewer.addHandler('open', function fitFirstPageToViewport() {
            const firstItem = viewer.world.getItemAt(0)
            if (firstItem) {
              viewer.viewport.fitBounds(firstItem.getBounds())
            }
          })
        } catch (error) {
          logger.error('Failed to initialize OSD viewer:', error)
        }
      })()

      return () => {
        cancelled = true
        if (viewer) {
          viewer.destroy()
          setViewer(null)
        }
      }
    },
    [tileSources, viewer]
  )

  return {
    containerRef,
    viewer,
  }
}
