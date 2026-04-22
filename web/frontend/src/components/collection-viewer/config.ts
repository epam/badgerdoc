import type { Options } from 'openseadragon'

export const ZOOM_IN_BTN_ID = 'viewer-zoom-in'
export const ZOOM_OUT_BTN_ID = 'viewer-zoom-out'
export const NEXT_BTN_ID = 'viewer-next'
export const PREV_BTN_ID = 'viewer-prev'

export const DEFAULT_OSD_CONFIG: Options = {
  // toolbar settings
  zoomInButton: ZOOM_IN_BTN_ID,
  zoomOutButton: ZOOM_OUT_BTN_ID,
  nextButton: NEXT_BTN_ID,
  previousButton: PREV_BTN_ID,
  // navigator settings
  showNavigator: true,
  navigatorPosition: 'TOP_LEFT',
  navigatorBackground: 'var(--muted)',
  navigatorOpacity: 0.95,
  navigatorBorderColor: 'var(--border)',
  navigatorDisplayRegionColor: 'var(--primary)',
  navigatorWidth: 120,
  navigatorHeight: 240,
  navigatorAutoFade: false,
  // viewer settings
  visibilityRatio: 1,
  maxZoomPixelRatio: 1,
  homeFillsViewer: false,
  minZoomImageRatio: 1,
  autoResize: true,  
  // Performance on iOS: snap pan/zoom to finger instead of using slow spring physics
  springStiffness: 15,
  animationTime: 0.4,
  gestureSettingsTouch: {
    flickEnabled: false,
    pinchToZoom: true,
  },
  // layout settings
  collectionMode: true,
  collectionRows: 1,
  collectionTileMargin: 20,
  collectionLayout: 'vertical',
}
