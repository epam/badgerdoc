/**
 * Mock Documents Data
 *
 * Centralized mock data for documents.
 * Previously inline in workspace/page.tsx (lines 36-44)
 */

import type { Document } from '@/shared/types/api'

// =============================================================================
// Mock Documents
// =============================================================================

export const mockDocuments: Document[] = [
  {
    id: '1',
    title: 'Material Composition for High-Temperature Applications',
    type: 'patent',
    status: 'analysis_ready',
    pdfUrl: '/sample.pdf',
    pageCount: 12,
    authors: ['J. Smith', 'A. Johnson', 'M. Williams'],
    publicationDate: '2024-01-15',
    abstract:
      'This patent describes a novel material composition optimized for high-temperature industrial applications.',
    metadata: {
      journal: 'Journal of Materials Science',
      doi: '10.1234/jms.2024.001',
    },
    createdAt: '2024-12-06T15:30:00Z',
    updatedAt: '2024-12-06T15:30:00Z',
    tags: [],
  },
  {
    id: '2',
    title: 'Novel Composite Material with Enhanced Optical Properties',
    type: 'paper',
    status: 'extraction_ready',
    pdfUrl: '/sample.pdf',
    pageCount: 18,
    authors: ['M. Chen', 'L. Wang'],
    publicationDate: '2024-02-20',
    abstract: 'A study on novel composite material compositions with enhanced optical properties.',
    metadata: {
      journal: 'Optical Materials',
      doi: '10.1234/om.2024.042',
    },
    createdAt: '2024-12-06T14:00:00Z',
    updatedAt: '2024-12-06T14:00:00Z',
    tags: ['ocr'],
  },
  {
    id: '3',
    title: 'Thermal Expansion Coefficient Optimization',
    type: 'paper',
    status: 'analysis_ready',
    pdfUrl: '/sample.pdf',
    pageCount: 15,
    authors: ['R. Brown', 'S. Davis', 'T. Wilson'],
    publicationDate: '2024-03-10',
    abstract: 'Research on optimizing thermal expansion coefficients in advanced materials.',
    metadata: {
      journal: 'Materials Technology',
      doi: '10.1234/gt.2024.018',
    },
    createdAt: '2024-12-05T10:00:00Z',
    updatedAt: '2024-12-05T10:00:00Z',
    tags: [],
  },
  {
    id: '4',
    title: 'Advanced Material Manufacturing Process',
    type: 'patent',
    status: 'extraction_approved',
    pdfUrl: '/sample.pdf',
    pageCount: 22,
    authors: ['K. Lee', 'P. Martinez'],
    publicationDate: '2024-04-05',
    abstract: 'An improved manufacturing process for advanced material production.',
    metadata: {
      doi: '10.5555/patent.2024.789',
    },
    createdAt: '2024-12-06T16:00:00Z',
    updatedAt: '2024-12-06T16:00:00Z',
    tags: ['ocr'],
  },
  {
    id: '5',
    title: 'Chemical Durability of Advanced Composite Materials',
    type: 'paper',
    status: 'completed',
    pdfUrl: '/sample.pdf',
    pageCount: 14,
    authors: ['E. Garcia', 'H. Nakamura'],
    publicationDate: '2024-05-12',
    abstract: 'Investigation of chemical durability in advanced composite material compositions.',
    metadata: {
      journal: 'Journal of Non-Crystalline Solids',
      doi: '10.1234/jncs.2024.055',
    },
    createdAt: '2024-12-04T09:00:00Z',
    updatedAt: '2024-12-06T12:00:00Z',
    processedAt: '2024-12-06T12:00:00Z',
    tags: [],
  },
]

// =============================================================================
// Helper Functions
// =============================================================================
