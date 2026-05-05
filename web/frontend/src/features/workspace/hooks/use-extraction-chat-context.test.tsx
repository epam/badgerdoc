import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  PROMPT_DRAFT_STORAGE_DEBOUNCE_MS,
  PROMPT_DRAFT_STORAGE_KEY,
  useExtractionChatContext,
} from './use-extraction-chat-context'

const originalLocalStorage = window.localStorage

describe('useExtractionChatContext prompt persistence', () => {
  beforeEach(() => {
    let storage = new Map<string, string>()

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: vi.fn((key: string) => storage.get(key) ?? null),
        setItem: vi.fn((key: string, value: string) => {
          storage.set(key, String(value))
        }),
        removeItem: vi.fn((key: string) => {
          storage.delete(key)
        }),
        clear: vi.fn(() => {
          storage = new Map<string, string>()
        }),
      },
    })

    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
    vi.restoreAllMocks()
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    })
  })

  it('restores a saved prompt draft from localStorage on mount', () => {
    const savedPrompt =
      "Analyze {{/badgerdoc/document/123/page/1}} and {{/badgerdoc/document/123/extraction/456/page/2/(//div[@id='block_2_1'])}}"

    window.localStorage.setItem(PROMPT_DRAFT_STORAGE_KEY, savedPrompt)

    const { result } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
      })
    )

    expect(result.current.prompt).toBe(savedPrompt)
    expect(result.current.selectedPages).toEqual([1])
    expect(result.current.selectedBlocks).toEqual([{ blockId: 'block_2_1', pageNumber: 2 }])
  })

  it('saves prompt changes with debounce', () => {
    const { result } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
      })
    )

    act(() => {
      result.current.setPrompt('Analyze {{/badgerdoc/document/123/page/1}}')
    })

    expect(window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)).toBeNull()

    act(() => {
      vi.advanceTimersByTime(PROMPT_DRAFT_STORAGE_DEBOUNCE_MS - 1)
    })

    expect(window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)).toBeNull()

    act(() => {
      vi.advanceTimersByTime(1)
    })

    expect(window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)).toBe(
      'Analyze {{/badgerdoc/document/123/page/1}}'
    )
  })

  it('keeps the current draft when switching documents', () => {
    const { result, rerender } = renderHook(
      ({ documentId }: { documentId: string }) =>
        useExtractionChatContext({
          documentId,
        }),
      {
        initialProps: { documentId: '123' },
      }
    )

    act(() => {
      result.current.setPrompt('Shared draft for every workspace')
    })

    rerender({ documentId: '456' })

    expect(result.current.prompt).toBe('Shared draft for every workspace')
  })

  it('keeps the current draft when switching extractions', () => {
    const extractionPages = [{ extraction_id: 456 }] as BadgerDocExtractionPage[]
    const nextExtractionPages = [{ extraction_id: 789 }] as BadgerDocExtractionPage[]
    const prompt =
      "Analyze {{/badgerdoc/document/123/extraction/456/page/2/(//div[@id='block_2_1'])}}"
    const { result, rerender } = renderHook(
      ({ pages }: { pages?: BadgerDocExtractionPage[] }) =>
        useExtractionChatContext({
          documentId: '123',
          extractionPages: pages,
        }),
      {
        initialProps: { pages: extractionPages },
      }
    )

    act(() => {
      result.current.setPrompt(prompt)
    })

    rerender({ pages: nextExtractionPages })

    expect(result.current.prompt).toBe(prompt)
    expect(result.current.selectedBlocks).toEqual([{ blockId: 'block_2_1', pageNumber: 2 }])
  })

  it('falls back to an empty prompt and keeps working when localStorage is unavailable', () => {
    vi.spyOn(window.localStorage, 'getItem').mockImplementation(() => {
      throw new Error('localStorage unavailable')
    })
    const setItemSpy = vi.spyOn(window.localStorage, 'setItem').mockImplementation(() => {
      throw new Error('localStorage unavailable')
    })

    const { result } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
      })
    )

    expect(result.current.prompt).toBe('')

    act(() => {
      result.current.setPrompt('Draft prompt')
    })

    expect(result.current.prompt).toBe('Draft prompt')

    expect(() => {
      act(() => {
        vi.advanceTimersByTime(PROMPT_DRAFT_STORAGE_DEBOUNCE_MS)
      })
    }).not.toThrow()

    expect(setItemSpy).toHaveBeenCalledWith(PROMPT_DRAFT_STORAGE_KEY, 'Draft prompt')
  })

  it('flushes the prompt draft to localStorage on unmount', () => {
    const { result, unmount } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
      })
    )

    act(() => {
      result.current.setPrompt('Unsaved draft')
    })

    // The debounce timer has NOT fired yet
    expect(window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)).toBeNull()

    unmount()

    expect(window.localStorage.getItem(PROMPT_DRAFT_STORAGE_KEY)).toBe('Unsaved draft')
  })

  it('removes committed block references from the prompt when requested', () => {
    const extractionPages = [{ extraction_id: 456 }] as BadgerDocExtractionPage[]
    const prompt = [
      "Keep {{/badgerdoc/document/123/extraction/456/page/2/(//div[@id='block_2_1'])}}",
      "and {{/badgerdoc/document/123/extraction/456/page/3/(//div[@id='block_3_1'])}}",
    ].join(' ')

    const { result } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
        extractionPages,
      })
    )

    act(() => {
      result.current.setPrompt(prompt)
    })

    act(() => {
      result.current.removeBlocks(['block_2_1'])
    })

    expect(result.current.prompt).toBe(
      "Keep  and {{/badgerdoc/document/123/extraction/456/page/3/(//div[@id='block_3_1'])}}"
    )
    expect(result.current.selectedBlocks).toEqual([{ blockId: 'block_3_1', pageNumber: 3 }])
  })

  it('ignores empty committed block cleanup requests', () => {
    const prompt = "Keep {{/badgerdoc/document/123/extraction/456/page/2/(//div[@id='block_2_1'])}}"
    const extractionPages = [{ extraction_id: 456 }] as BadgerDocExtractionPage[]
    const { result } = renderHook(() =>
      useExtractionChatContext({
        documentId: '123',
        extractionPages,
      })
    )

    act(() => {
      result.current.setPrompt(prompt)
    })

    act(() => {
      result.current.removeBlocks([])
    })

    expect(result.current.prompt).toBe(prompt)
    expect(result.current.selectedBlocks).toEqual([{ blockId: 'block_2_1', pageNumber: 2 }])
  })
})
