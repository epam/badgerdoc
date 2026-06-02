import { useEffect, useMemo, useRef, useState } from 'react'
import OpenSeadragon, { Options, Viewer as OSDViewer } from 'openseadragon'
import { logger } from '@/shared/logger.ts'
import { DEFAULT_OSD_CONFIG, MACOS_OSD_CONFIG } from '@/components/collection-viewer/config'
import { isMacOS } from '@/helpers/utils'
import type { PageSource } from '@/shared/api/badgerdoc/types'

type OsdTileSource = string | { type: 'image'; url: string }

const toOsdTileSource = (page: PageSource): OsdTileSource =>
  page.type === 'image' ? { type: 'image', url: page.url } : page.url

interface UseOsdViewerOptions {
  /**
   * Fired when OpenSeadragon reports that a tile source failed to initialize
   * (the 'open-failed' event). Used as a runtime safety net so the caller can
   * switch to PNG fallback when DZI assets are broken at the storage level
   * but were still listed by the API.
   */
  onLoadFailed?: () => void
}

export const useOsdViewer = (pages?: PageSource[], options?: UseOsdViewerOptions) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [viewer, setViewer] = useState<OSDViewer | null>(null)

  const tileSources = useMemo(() => pages?.map(toOsdTileSource), [pages])

  // Keep the callback in a ref so changes in the caller's closure identity
  // don't tear down and rebuild the viewer.
  const onLoadFailedRef = useRef(options?.onLoadFailed)
  useEffect(() => {
    onLoadFailedRef.current = options?.onLoadFailed
  }, [options?.onLoadFailed])

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

        osdViewer.addHandler('open-failed', function handleOpenFailed(event) {
          logger.warn('OSD failed to open tile source, requesting PNG fallback', event)
          onLoadFailedRef.current?.()
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
