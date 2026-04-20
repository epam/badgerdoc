export type TaskSortBy = 'newest' | 'oldest'
export type TaskTypeFilter = 'all' | 'patent' | 'paper' | 'article'

export interface TaskFilters {
  query: string
  activeTab: string
  sortBy: TaskSortBy
  typeFilter: TaskTypeFilter
  dateFrom: Date | null
  dateTo: Date | null
}

export interface TaskFiltersSearch {
  q?: string
  status?: string
  sort?: TaskSortBy
  type?: TaskTypeFilter
  from?: string
  to?: string
}

export const DEFAULT_TASK_FILTERS: TaskFilters = {
  query: '',
  activeTab: 'all',
  sortBy: 'newest',
  typeFilter: 'all',
  dateFrom: null,
  dateTo: null,
}

const SORT_VALUES: TaskSortBy[] = ['newest', 'oldest']
const TYPE_VALUES: TaskTypeFilter[] = ['all', 'patent', 'paper', 'article']
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/

function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value.trim() : undefined
}

function parseDate(value: string | undefined): Date | null {
  if (!value || !DATE_RE.test(value)) return null
  const parsed = new Date(`${value}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatDate(value: Date): string {
  const year = value.getFullYear()
  const month = `${value.getMonth() + 1}`.padStart(2, '0')
  const day = `${value.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function normalizeTaskFiltersSearch(search: Record<string, unknown>): TaskFiltersSearch {
  const q = asString(search.q)
  const status = asString(search.status)
  const sort = asString(search.sort)
  const type = asString(search.type)
  const from = asString(search.from)
  const to = asString(search.to)

  return {
    q,
    status,
    sort: SORT_VALUES.includes(sort as TaskSortBy) ? (sort as TaskSortBy) : undefined,
    type: TYPE_VALUES.includes(type as TaskTypeFilter) ? (type as TaskTypeFilter) : undefined,
    from: parseDate(from) ? from : undefined,
    to: parseDate(to) ? to : undefined,
  }
}

export function taskFiltersFromSearch(search: TaskFiltersSearch): TaskFilters {
  const normalized = normalizeTaskFiltersSearch(search as Record<string, unknown>)

  return {
    query: normalized.q ?? DEFAULT_TASK_FILTERS.query,
    activeTab: normalized.status ?? DEFAULT_TASK_FILTERS.activeTab,
    sortBy: normalized.sort ?? DEFAULT_TASK_FILTERS.sortBy,
    typeFilter: normalized.type ?? DEFAULT_TASK_FILTERS.typeFilter,
    dateFrom: parseDate(normalized.from),
    dateTo: parseDate(normalized.to),
  }
}

export function taskFiltersToSearch(filters: TaskFilters): TaskFiltersSearch {
  return {
    q: filters.query || undefined,
    status: filters.activeTab !== DEFAULT_TASK_FILTERS.activeTab ? filters.activeTab : undefined,
    sort: filters.sortBy !== DEFAULT_TASK_FILTERS.sortBy ? filters.sortBy : undefined,
    type: filters.typeFilter !== DEFAULT_TASK_FILTERS.typeFilter ? filters.typeFilter : undefined,
    from: filters.dateFrom ? formatDate(filters.dateFrom) : undefined,
    to: filters.dateTo ? formatDate(filters.dateTo) : undefined,
  }
}
