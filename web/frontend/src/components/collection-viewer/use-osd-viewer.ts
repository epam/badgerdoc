import { useEffect, useRef, useState } from 'react'
import OpenSeadragon, { Options, Viewer as OSDViewer } from 'openseadragon'
import { logger } from '@/shared/logger.ts'
import { DEFAULT_OSD_CONFIG, MACOS_OSD_CONFIG } from '@/components/collection-viewer/config'
import { isMacOS } from '@/helpers/utils'

export const useOsdViewer = (tileSources?: string[]) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [viewer, setViewer] = useState<OSDViewer | null>(null)

  useEffect(
    function initViewerForDocument() {
      if (!containerRef.current) return

      let osdViewer: OSDViewer | null = null
      const platformConfig = isMacOS() ? MACOS_OSD_CONFIG : {}

      try {
        osdViewer = new OpenSeadragon.Viewer({
          element: containerRef.current,
          ...DEFAULT_OSD_CONFIG,
          ...platformConfig,
          tileSources,
        } as Partial<Options>)
        setViewer(osdViewer)

        osdViewer.addHandler('open', function fitFirstPageToViewport() {
          const firstItem = osdViewer?.world.getItemAt(0)
          if (firstItem) {
            osdViewer?.viewport.fitBounds(firstItem.getBounds())
          }
        })
      } catch (error) {
        logger.error('Failed to initialize OSD viewer:', error)
      }

      return () => {
        if (osdViewer) {
          osdViewer.destroy()
        }
        setViewer((currentViewer) => (currentViewer === osdViewer ? null : currentViewer))
      }
    },
    [tileSources]
  )

  return {
    containerRef,
    viewer,
  }
}
