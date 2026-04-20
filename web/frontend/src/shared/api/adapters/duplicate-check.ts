/**
 * Duplicate Check Adapter
 *
 * Handles duplicate check decisions with localStorage persistence.
 * Easy to switch to a real API implementation later.
 */

import type { DuplicateCheckStatus } from '@/shared/api/badgerdoc/types'

const STORAGE_KEY = 'duplicate-check-decisions'

interface DuplicateDecision {
  documentId: string
  status: DuplicateCheckStatus
  decidedAt: string
}

interface SimilarDocument {
  id: string
  title: string
  authors: string[]
  journal?: string
  year?: number
  doi?: string
  abstract?: string
  type: string
  similarity_score: number
}

interface DuplicateCheckAdapter {
  getDecision(documentId: string): Promise<DuplicateDecision | null>
  getAllDecisions(): Promise<Record<string, DuplicateDecision>>
  submitDecision(documentId: string, status: DuplicateCheckStatus): Promise<DuplicateDecision>
  clearDecision(documentId: string): Promise<void>
  clearAll(): Promise<void>
  getSimilarDocument(documentId: string): Promise<SimilarDocument | null>
}

/**
 * localStorage-based implementation for development/testing
 */
function createLocalStorageAdapter(): DuplicateCheckAdapter {
  function getStoredDecisions(): Record<string, DuplicateDecision> {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : {}
    } catch {
      return {}
    }
  }

  function saveDecisions(decisions: Record<string, DuplicateDecision>): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(decisions))
  }

  return {
    async getDecision(documentId: string): Promise<DuplicateDecision | null> {
      const decisions = getStoredDecisions()
      return decisions[documentId] || null
    },

    async getAllDecisions(): Promise<Record<string, DuplicateDecision>> {
      return getStoredDecisions()
    },

    async submitDecision(
      documentId: string,
      status: DuplicateCheckStatus
    ): Promise<DuplicateDecision> {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 300))

      const decision: DuplicateDecision = {
        documentId,
        status,
        decidedAt: new Date().toISOString(),
      }

      const decisions = getStoredDecisions()
      decisions[documentId] = decision
      saveDecisions(decisions)

      return decision
    },

    async clearDecision(documentId: string): Promise<void> {
      const decisions = getStoredDecisions()
      delete decisions[documentId]
      saveDecisions(decisions)
    },

    async clearAll(): Promise<void> {
      localStorage.removeItem(STORAGE_KEY)
    },

    async getSimilarDocument(_documentId: string): Promise<SimilarDocument | null> {
      // Mock similar document data for comparison
      // In production, this would fetch from an API endpoint
      return {
        id: 'similar-doc-001',
        title: 'Advanced Material Compositions for Industrial Applications',
        authors: ['J. Smith'],
        journal: 'Materials Science & Engineering',
        year: 2023,
        doi: '10.1234/materials.2023.xyz',
        abstract:
          'This paper presents novel material compositions designed for high-temperature industrial applications. The compositions exhibit excellent thermal stability and mechanical properties suitable for demanding environments.',
        type: 'article',
        similarity_score: 92,
      }
    },
  }
}

/**
 * Real API implementation (placeholder)
 * Uncomment and implement when backend is ready
 */
// function createRealApiAdapter(): DuplicateCheckAdapter {
//   return {
//     async getDecision(documentId: string): Promise<DuplicateDecision | null> {
//       const response = await fetch(`/api/documents/${documentId}/duplicate-status`)
//       if (!response.ok) return null
//       return response.json()
//     },
//     async getAllDecisions(): Promise<Record<string, DuplicateDecision>> {
//       const response = await fetch('/api/documents/duplicate-decisions')
//       return response.json()
//     },
//     async submitDecision(documentId: string, status: DuplicateCheckStatus): Promise<DuplicateDecision> {
//       const response = await fetch(`/api/documents/${documentId}/duplicate-decision`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ status }),
//       })
//       return response.json()
//     },
//     async clearDecision(documentId: string): Promise<void> {
//       await fetch(`/api/documents/${documentId}/duplicate-decision`, { method: 'DELETE' })
//     },
//     async clearAll(): Promise<void> {
//       // Not typically needed for real API
//     },
//   }
// }

// Switch this when backend is ready:
// export const duplicateCheckAdapter = createRealApiAdapter()
export const duplicateCheckAdapter = createLocalStorageAdapter()
