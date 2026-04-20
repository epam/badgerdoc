import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
;(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver =
  ResizeObserverMock as unknown as typeof ResizeObserver

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
  root = null
  rootMargin = ''
  thresholds = []
}
;(
  globalThis as unknown as { IntersectionObserver: typeof IntersectionObserver }
).IntersectionObserver = IntersectionObserverMock as unknown as typeof IntersectionObserver

// Default API handlers for MSW
export const handlers = [
  http.get('/api/documents', () => {
    return HttpResponse.json({
      data: [],
      meta: { total: 0, page: 1, pageSize: 20 },
    })
  }),
  http.get('/api/documents/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: 'Test Document',
      type: 'paper',
      status: 'pending_analysis',
    })
  }),
  http.get('/api/documents/:id/extraction', ({ params }) => {
    return HttpResponse.json({
      id: `ext-${params.id}`,
      documentId: params.id,
      status: 'ready',
      fields: [],
      tables: [],
    })
  }),
  http.get('/api/documents/:id/analysis', ({ params }) => {
    return HttpResponse.json({
      id: `analysis-${params.id}`,
      documentId: params.id,
      findings: [],
      summary: { totalFindings: 0, averageConfidence: 0 },
    })
  }),
]

// Setup MSW server
export const server = setupServer(...handlers)

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
