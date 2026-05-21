import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useExtractionApi, withUserInputTag } from './use-extraction-api'
import { extractionPagesKeys } from '@/shared/api/hooks'

const { extractionsAdapter } = vi.hoisted(() => ({
  extractionsAdapter: {
    getLatestExtraction: vi.fn(),
    createExtraction: vi.fn(),
    createExtractionPage: vi.fn(),
    updateExtractionPage: vi.fn(),
    updateExtraction: vi.fn(),
  },
}))

vi.mock('@/shared/api/adapters/factory', () => ({
  getApiAdapter: () => ({
    extractions: extractionsAdapter,
  }),
}))

function createWrapper(queryClient = new QueryClient()) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('withUserInputTag', () => {
  it('preserves existing tags and appends user-input once', () => {
    expect(withUserInputTag(['paddle-ocr', 'reviewed', 'user-input'])).toEqual([
      'paddle-ocr',
      'reviewed',
      'user-input',
    ])
  })
})

describe('useExtractionApi', () => {
  beforeEach(() => {
    extractionsAdapter.getLatestExtraction.mockReset()
    extractionsAdapter.createExtraction.mockReset()
    extractionsAdapter.createExtractionPage.mockReset()
    extractionsAdapter.updateExtractionPage.mockReset()
    extractionsAdapter.updateExtraction.mockReset()

    extractionsAdapter.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 123,
      status: 'Started',
      tags: ['paddle-ocr'],
    })
    extractionsAdapter.updateExtractionPage.mockResolvedValue({
      id: 1,
      extraction_id: 45,
      page_number: 1,
      content: '<html></html>',
    })
    extractionsAdapter.updateExtraction.mockResolvedValue({
      id: 45,
      document_id: 123,
      status: 'Completed',
      tags: ['paddle-ocr', 'user-input'],
    })
  })

  it('adds user-input when creating an extraction for user edits', async () => {
    const { result } = renderHook(
      () => useExtractionApi({ documentId: '123', activeTag: 'paddle-ocr' }),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      await result.current.saveExtractionPages([{ page: 1, hocr: '<html></html>' }])
    })

    expect(extractionsAdapter.createExtraction).toHaveBeenCalledWith({
      documentId: '123',
      status: 'Started',
      tags: ['paddle-ocr', 'user-input'],
    })
  })

  it('keeps user-input deduplicated when completing edited extraction data', async () => {
    extractionsAdapter.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 123,
      status: 'Started',
      tags: ['paddle-ocr', 'user-input'],
    })

    const { result } = renderHook(
      () => useExtractionApi({ documentId: '123', activeTag: 'paddle-ocr' }),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      await result.current.acceptExtraction([{ page: 1, hocr: '<html></html>' }])
    })

    expect(extractionsAdapter.updateExtraction).toHaveBeenCalledWith({
      extractionId: 45,
      status: 'Completed',
      tags: ['paddle-ocr', 'user-input'],
    })
  })

  it('creates an extraction only once across multiple saves', async () => {
    const queryClient = new QueryClient()
    const wrapper = createWrapper(queryClient)

    extractionsAdapter.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractionsAdapter.updateExtractionPage.mockResolvedValue({})

    const { result } = renderHook(
      () =>
        useExtractionApi({
          documentId: 'doc-1',
          activeTag: 'deepseek-ocr-2',
        }),
      { wrapper }
    )

    await act(async () => {
      await result.current.saveExtractionPages([{ page: 1, hocr: '<p>one</p>' }])
      await result.current.saveExtractionPages([{ page: 2, hocr: '<p>two</p>' }])
    })

    expect(extractionsAdapter.createExtraction).toHaveBeenCalledTimes(1)
    expect(extractionsAdapter.updateExtractionPage).toHaveBeenNthCalledWith(1, {
      extractionId: 45,
      pageNumber: 1,
      content: '<p>one</p>',
    })
    expect(extractionsAdapter.updateExtractionPage).toHaveBeenNthCalledWith(2, {
      extractionId: 45,
      pageNumber: 2,
      content: '<p>two</p>',
    })
  })

  it('falls back to createExtractionPage when updating a page fails', async () => {
    const queryClient = new QueryClient()
    const wrapper = createWrapper(queryClient)

    extractionsAdapter.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractionsAdapter.updateExtractionPage.mockRejectedValueOnce(new Error('missing page'))
    extractionsAdapter.createExtractionPage.mockResolvedValue({})

    const { result } = renderHook(
      () =>
        useExtractionApi({
          documentId: 'doc-1',
          activeTag: 'deepseek-ocr-2',
        }),
      { wrapper }
    )

    await act(async () => {
      await result.current.saveExtractionPages([{ page: 1, hocr: '<p>one</p>' }])
    })

    expect(extractionsAdapter.createExtractionPage).toHaveBeenCalledWith({
      extractionId: 45,
      pageNumber: 1,
      content: '<p>one</p>',
    })
  })

  it('accepts extraction changes and invalidates the extraction pages query', async () => {
    const queryClient = new QueryClient()
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')
    const wrapper = createWrapper(queryClient)

    extractionsAdapter.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractionsAdapter.updateExtractionPage.mockResolvedValue({})
    extractionsAdapter.updateExtraction.mockResolvedValue({})

    const { result } = renderHook(
      () =>
        useExtractionApi({
          documentId: 'doc-1',
          activeTag: 'deepseek-ocr-2',
        }),
      { wrapper }
    )

    await act(async () => {
      await result.current.acceptExtraction([{ page: 1, hocr: '<p>one</p>' }])
    })

    expect(extractionsAdapter.updateExtraction).toHaveBeenCalledWith({
      extractionId: 45,
      status: 'Completed',
      tags: ['deepseek-ocr-2', 'user-input'],
    })
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: extractionPagesKeys.documentWithTags('doc-1', 'deepseek-ocr-2'),
    })
  })
})
