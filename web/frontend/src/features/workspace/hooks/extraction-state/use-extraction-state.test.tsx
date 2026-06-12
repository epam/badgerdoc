import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useExtractionState } from './use-extraction-state'

describe('useExtractionState', () => {
  it('builds a pending payload when the first extraction block is created', () => {
    const { result } = renderHook(() =>
      useExtractionState({
        extractionPages: [],
        activeTag: 'analysis',
      })
    )

    act(() => {
      result.current.handleBlockCreate(0, {
        x: 0.1,
        y: 0.2,
        width: 0.3,
        height: 0.4,
      })
    })

    expect(result.current.hasChanges).toBe(true)
    expect(result.current.pendingPayload).toHaveLength(1)
    expect(result.current.pendingPayload[0].page).toBe(1)
    expect(result.current.pendingPayload[0].hocr).toContain(
      '<meta name="ocr-system" content="analysis"/>'
    )
    expect(result.current.pendingPayload[0].hocr).toContain('id="block_1_1"')
    expect(result.current.pendingPayload[0].hocr).toContain('bbox 100 200 400 600')
  })
})
