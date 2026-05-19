import { describe, expect, it } from 'vitest'
import {
  formatLogTime,
  hasMeaningfulWorkflowParams,
  safeStringify,
  shouldShowSourceDocumentLink,
} from './agent-log-entry'

describe('agent-log-entry helpers', () => {
  it.each([undefined, null, {}, [], '', '   '])(
    'treats %s as empty workflow params',
    (value) => {
      expect(hasMeaningfulWorkflowParams(value)).toBe(false)
    }
  )

  it.each([{ model: 'test' }, ['item'], true, false, 0, 'value'])(
    'treats %s as meaningful workflow params',
    (value) => {
      expect(hasMeaningfulWorkflowParams(value)).toBe(true)
    }
  )

  it('stringifies circular values safely', () => {
    const value: { self?: unknown } = {}
    value.self = value

    expect(safeStringify(value)).toContain('"self": "[Circular]"')
  })

  it('returns invalid timestamps unchanged', () => {
    expect(formatLogTime('not-a-date')).toBe('not-a-date')
  })

  it('does not show a source document link for current-document logs', () => {
    expect(
      shouldShowSourceDocumentLink({
        currentDocumentId: '123',
        sourceDocumentId: 123,
      })
    ).toBe(false)
  })

  it('shows a source document link for child-document logs', () => {
    expect(
      shouldShowSourceDocumentLink({
        currentDocumentId: '123',
        sourceDocumentId: 456,
      })
    ).toBe(true)
  })
})
