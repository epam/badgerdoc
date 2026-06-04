import { describe, expect, it } from 'vitest'
import {
  formatLogTime,
  getWorkflowHeaderLabel,
  hasMeaningfulWorkflowParams,
  safeStringify,
  shouldShowSourceDocumentLink,
} from './agent-log-entry'

describe('agent-log-entry helpers', () => {
  it.each([undefined, null, {}, [], '', '   ', { llm_params: '', options: {} }, [null, {}]])(
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

  it('returns a compact workflow header label from workflow metadata', () => {
    expect(
      getWorkflowHeaderLabel({
        workflow: {
          name: 'Mineru OCR',
          trigger: 'manual',
          id: 12,
        },
      })
    ).toBe('Mineru OCR · manual')
  })

  it('omits workflow trigger from the header label when it is missing', () => {
    expect(
      getWorkflowHeaderLabel({
        workflow: {
          name: 'Mineru OCR',
        },
      })
    ).toBe('Mineru OCR')
  })

  it('does not return a workflow header label without a workflow name', () => {
    expect(getWorkflowHeaderLabel({ workflow: { trigger: 'manual' } })).toBeNull()
    expect(getWorkflowHeaderLabel({ workflow: null })).toBeNull()
  })
})
