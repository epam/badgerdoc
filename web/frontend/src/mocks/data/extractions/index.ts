import page1 from './page_1.hocr'
import page2 from './page_2.hocr'
import page3 from './page_3.hocr'
import { BadgerDocExtraction, BadgerDocExtractionPage } from '@/shared/api/badgerdoc'

export const extractionPageMocksByNumber: Record<number, string> = {
  1: page1,
  2: page2,
  3: page3,
}

export const extractionMock: BadgerDocExtractionPage[] = [
  {
    page_number: 1,
    content: page1,
  },
  {
    page_number: 2,
    content: page2,
  },
  {
    page_number: 3,
    content: page3,
  },
]

export const createExtractionMock: BadgerDocExtraction = {
  id: 45,
  document_id: 6,
  created_by: 'admin',
  status: 'Pending',
  temporal_job_id: null,
  comment: '',
  tags: ['deepseek-ocr-2'],
  created_at: '2026-03-27T06:17:46.420137Z',
  updated_at: '2026-03-27T06:17:46.420153Z',
}

export const extractionPageMock: BadgerDocExtractionPage = {
  id: 44,
  extraction_id: 45,
  page_number: 1,
  content: page1,
  created_at: '2026-03-27T06:17:46.454317Z',
  updated_at: '2026-03-27T06:17:46.454328Z',
}
