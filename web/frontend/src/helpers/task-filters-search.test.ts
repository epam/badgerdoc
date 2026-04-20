import { describe, expect, it } from 'vitest'
import {
  DEFAULT_TASK_FILTERS,
  normalizeTaskFiltersSearch,
  taskFiltersFromSearch,
  taskFiltersToSearch,
  type TaskFilters,
} from './task-filters-search'

describe('task-filters-search helper', () => {
  describe('normalizeTaskFiltersSearch', () => {
    it('keeps supported values and trims text fields', () => {
      const normalized = normalizeTaskFiltersSearch({
        q: '  duplicate review  ',
        status: '  completed  ',
        sort: 'oldest',
        type: 'paper',
        from: '2026-01-15',
        to: '2026-01-31',
      })

      expect(normalized).toEqual({
        q: 'duplicate review',
        status: 'completed',
        sort: 'oldest',
        type: 'paper',
        from: '2026-01-15',
        to: '2026-01-31',
      })
    })

    it('drops invalid sort/type/date values', () => {
      const normalized = normalizeTaskFiltersSearch({
        sort: 'random-order',
        type: 'book',
        from: '15-01-2026',
        to: '2026-13-99',
      })

      expect(normalized.sort).toBeUndefined()
      expect(normalized.type).toBeUndefined()
      expect(normalized.from).toBeUndefined()
      expect(normalized.to).toBeUndefined()
    })
  })

  describe('taskFiltersFromSearch', () => {
    it('returns defaults for empty search', () => {
      expect(taskFiltersFromSearch({})).toEqual(DEFAULT_TASK_FILTERS)
    })

    it('parses dates from search params', () => {
      const filters = taskFiltersFromSearch({
        from: '2026-02-10',
        to: '2026-02-20',
      })

      expect(filters.dateFrom).not.toBeNull()
      expect(filters.dateTo).not.toBeNull()
      expect(filters.dateFrom?.getFullYear()).toBe(2026)
      expect(filters.dateFrom?.getMonth()).toBe(1)
      expect(filters.dateFrom?.getDate()).toBe(10)
      expect(filters.dateTo?.getFullYear()).toBe(2026)
      expect(filters.dateTo?.getMonth()).toBe(1)
      expect(filters.dateTo?.getDate()).toBe(20)
    })
  })

  describe('taskFiltersToSearch', () => {
    it('omits default values from query object', () => {
      expect(taskFiltersToSearch(DEFAULT_TASK_FILTERS)).toEqual({
        q: undefined,
        status: undefined,
        sort: undefined,
        type: undefined,
        from: undefined,
        to: undefined,
      })
    })

    it('serializes non-default filters into compact search params', () => {
      const filters: TaskFilters = {
        query: 'invoice batch',
        activeTab: 'completed',
        sortBy: 'oldest',
        typeFilter: 'paper',
        dateFrom: new Date('2026-03-01T00:00:00'),
        dateTo: new Date('2026-03-07T00:00:00'),
      }

      expect(taskFiltersToSearch(filters)).toEqual({
        q: 'invoice batch',
        status: 'completed',
        sort: 'oldest',
        type: 'paper',
        from: '2026-03-01',
        to: '2026-03-07',
      })
    })
  })

  it('supports roundtrip conversion for a full non-default filter set', () => {
    const original: TaskFilters = {
      query: 'priority queue',
      activeTab: 'in-progress',
      sortBy: 'oldest',
      typeFilter: 'article',
      dateFrom: new Date('2026-04-10T00:00:00'),
      dateTo: new Date('2026-04-15T00:00:00'),
    }

    const search = taskFiltersToSearch(original)
    const parsed = taskFiltersFromSearch(search)

    expect(parsed.query).toBe(original.query)
    expect(parsed.activeTab).toBe(original.activeTab)
    expect(parsed.sortBy).toBe(original.sortBy)
    expect(parsed.typeFilter).toBe(original.typeFilter)
    expect(parsed.dateFrom?.toISOString()).toBe(original.dateFrom?.toISOString())
    expect(parsed.dateTo?.toISOString()).toBe(original.dateTo?.toISOString())
  })
})
