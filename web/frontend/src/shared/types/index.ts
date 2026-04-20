import type { ConfidenceLevel } from './api'

export interface User {
  id: number
  name: string
  role: 'admin' | 'reviewer' | 'viewer'
  username: string
}

export interface AIHint {
  id: string
  documentId: string
  content: string
  pageNumber: number
  boundingBox?: BoundingBox
  confidence: ConfidenceLevel
  category: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

// Re-export API types
export * from './api'

// Re-export tasks types
export * from './tasks'
