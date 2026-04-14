import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import { type ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useExtractionApi } from './use-extraction-api'
import { extractionPagesKeys } from '@/shared/api/hooks'
import { getApiAdapter } from '@/shared/api/adapters/factory'

vi.mock('@/shared/api/adapters/factory', () => ({
  getApiAdapter: vi.fn(),
}))

const mockedGetApiAdapter = vi.mocked(getApiAdapter)

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useExtractionApi', () => {
  const extractions = {
    createExtraction: vi.fn(),
    updateExtractionPage: vi.fn(),
    createExtractionPage: vi.fn(),
    updateExtraction: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetApiAdapter.mockReturnValue({
      extractions,
    } as ReturnType<typeof getApiAdapter>)
  })

  it('creates an extraction only once across multiple saves', async () => {
    const queryClient = new QueryClient()
    const wrapper = createWrapper(queryClient)

    extractions.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractions.updateExtractionPage.mockResolvedValue({})

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

    expect(extractions.createExtraction).toHaveBeenCalledTimes(1)
    expect(extractions.updateExtractionPage).toHaveBeenNthCalledWith(1, {
      extractionId: 45,
      pageNumber: 1,
      content: '<p>one</p>',
    })
    expect(extractions.updateExtractionPage).toHaveBeenNthCalledWith(2, {
      extractionId: 45,
      pageNumber: 2,
      content: '<p>two</p>',
    })
  })

  it('falls back to createExtractionPage when updating a page fails', async () => {
    const queryClient = new QueryClient()
    const wrapper = createWrapper(queryClient)

    extractions.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractions.updateExtractionPage.mockRejectedValueOnce(new Error('missing page'))
    extractions.createExtractionPage.mockResolvedValue({})

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

    expect(extractions.createExtractionPage).toHaveBeenCalledWith({
      extractionId: 45,
      pageNumber: 1,
      content: '<p>one</p>',
    })
  })

  it('accepts extraction changes and invalidates the extraction pages query', async () => {
    const queryClient = new QueryClient()
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')
    const wrapper = createWrapper(queryClient)

    extractions.createExtraction.mockResolvedValue({
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: ['deepseek-ocr-2'],
    })
    extractions.updateExtractionPage.mockResolvedValue({})
    extractions.updateExtraction.mockResolvedValue({})

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

    expect(extractions.updateExtraction).toHaveBeenCalledWith({
      extractionId: 45,
      status: 'Completed',
    })
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: extractionPagesKeys.documentWithTags('doc-1', 'deepseek-ocr-2'),
    })
  })
})
