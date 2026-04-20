/**
 * Tasks Hooks
 *
 * React Query hooks for the Tasks API.
 * Provides data fetching and mutations for task management.
 */

import { useQuery } from '@tanstack/react-query'
import { getApiAdapter } from '../adapters/factory'
import { getTaskActionLabel, Task, TasksListParams, TasksQueueParams } from '@/shared/types/tasks'
import { useMemo } from 'react'
import type { ConfidenceLevel } from '@/shared/types'
import { extractFilenameFromUrl } from '@/helpers/utils'
import type { TaskFilters } from '@/helpers/task-filters-search'

// =============================================================================
// Query Keys
// =============================================================================

const tasksKeys = {
  all: ['tasks'] as const,
  lists: () => [...tasksKeys.all, 'list'] as const,
  list: (params?: TasksListParams) => [...tasksKeys.lists(), params] as const,
  details: () => [...tasksKeys.all, 'detail'] as const,
  detail: (id: number) => [...tasksKeys.details(), id] as const,
  statuses: () => [...tasksKeys.all, 'statuses'] as const,
  nextStatuses: (id: number) => [...tasksKeys.all, 'nextStatuses', id] as const,
}

// =============================================================================
// Query Hooks
// =============================================================================

export interface SearchDocument {
  id: string
  taskId: number
  extractionId?: number
  title: string
  filename: string
  type: 'patent' | 'paper' | 'article'
  status: string
  statusId: number
  statusName: string
  confidence: ConfidenceLevel
  authors: string[]
  date: string
  createdAt: string
  priority?: 'high' | 'normal'
  actionLabel: string
  workspaceTag: string
}

// Transform Task to SearchDocument for backward compatibility with existing UI
function transformTaskToSearchDocument(task: Task): SearchDocument {
  const metadata = task.document.metadata || {}

  const filename = extractFilenameFromUrl(task.document.file)
  const title = (metadata.title as string) || filename || `Document ${task.document.id}`

  const rawType = (metadata.type as string)?.toLowerCase() || 'paper'
  const type = ['patent', 'paper', 'article'].includes(rawType)
    ? (rawType as 'patent' | 'paper' | 'article')
    : 'paper'

  const rawAuthor = metadata.author || metadata.authors
  const authors: string[] = Array.isArray(rawAuthor)
    ? rawAuthor
    : typeof rawAuthor === 'string'
      ? rawAuthor
          .split(',')
          .map((a: string) => a.trim())
          .filter(Boolean)
      : []

  const rawDate = (metadata.date as string) || task.created_at
  const date = rawDate.split('T')[0]

  const confidence = (metadata.confidence as ConfidenceLevel) || 'Medium'
  const priority = (metadata.priority as 'high' | 'normal') || 'normal'

  return {
    id: String(task.document.id),
    taskId: task.id,
    extractionId: task.extractions[0]?.id,
    title,
    filename,
    type,
    status: task.status.name, // Use status name directly as tab ID
    statusId: task.status.id,
    statusName: task.status.name,
    confidence,
    authors,
    date,
    createdAt: task.created_at,
    priority,
    actionLabel: getTaskActionLabel(task.status.id),
    workspaceTag: 'overview',
  }
}

/**
 * Fetch paginated list of tasks with optional filtering
 *
 * @example
 * const { data, isLoading } = useTasks({ status: 'New Task', page_size: 20 })
 */
function useTasks(params?: TasksListParams, enabled: boolean = true) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: tasksKeys.list(params),
    queryFn: () => adapter.tasks.list(params),
    enabled,
    staleTime: 30000, // 30 seconds
  })
}

const toStartOfDay = (date: Date) => {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

const toEndOfDay = (date: Date) => {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d
}

function formatDateRangeForRequest(
  dateFrom: Date | null,
  dateTo: Date | null
): Partial<TasksListParams> {
  const formatted: Partial<TasksListParams> = {}

  if (dateFrom) {
    formatted.created_at__gte = toStartOfDay(dateFrom).toISOString()
  }
  if (dateTo) {
    formatted.created_at__lte = toEndOfDay(dateTo).toISOString()
  }

  return formatted
}

export function useFilteredTasks(
  filters: TaskFilters,
  params?: TasksListParams,
  enabled: boolean = true
) {
  const { activeTab, typeFilter, query, sortBy, dateTo, dateFrom } = filters
  const { data: statuses } = useTaskStatuses(enabled)
  const statusFilter = activeTab !== 'all' ? activeTab : undefined
  const statusId = statuses?.find((s) => s.name === statusFilter)?.id

  const rawTasks = useTasks(
    {
      ...formatDateRangeForRequest(dateFrom, dateTo),
      status_id: statusId,
      ...params,
    },
    enabled
  )

  const formattedTasks = useMemo(() => {
    const results = rawTasks.data?.results ?? []
    return results.map(transformTaskToSearchDocument)
  }, [rawTasks.data?.results])

  const filteredTasks = useMemo(() => {
    return formattedTasks.filter((task) => {
      if (activeTab !== 'all' && task.status !== activeTab) {
        return false
      }

      if (typeFilter !== 'all' && task.type !== typeFilter) {
        return false
      }

      if (query) {
        const q = query.toLowerCase()
        if (
          !task.title.toLowerCase().includes(q) &&
          !task.authors.some((a) => a.toLowerCase().includes(q))
        ) {
          return false
        }
      }

      return true
    })
  }, [formattedTasks, activeTab, typeFilter, query])

  const sortedTasks = useMemo(() => {
    return [...filteredTasks].sort((a, b) => {
      switch (sortBy) {
        case 'oldest':
          return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        default:
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      }
    })
  }, [filteredTasks, sortBy])

  return {
    ...rawTasks,
    data: {
      ...rawTasks.data,
      results: sortedTasks,
    },
  }
}

interface UseTasksQueueParams extends TasksQueueParams {
  filters: TaskFilters
}

export function useTasksQueue(params: UseTasksQueueParams) {
  const { currentTaskId, filters, ...queryParams } = params
  const tasksQuery = useFilteredTasks(filters, queryParams, currentTaskId > 0)

  const position = tasksQuery.data?.results.findIndex((task) => task.taskId === currentTaskId) ?? -1

  return {
    ...tasksQuery,
    data: {
      position: position >= 0 ? position + 1 : undefined,
      total: tasksQuery.data?.results?.length, // use length of filtered results for total instead of the API's count
      prevId: position > 0 ? tasksQuery.data?.results[position - 1].taskId : null,
      nextId:
        position >= 0 && position < (tasksQuery.data?.results.length ?? 0) - 1
          ? tasksQuery.data?.results[position + 1].taskId
          : null,
    },
  }
}

/**
 * Fetch a single task by ID
 *
 * @example
 * const { data: task } = useTask(123)
 */
export function useTask(taskId: number) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: tasksKeys.detail(taskId),
    queryFn: () => adapter.tasks.getById(taskId),
    enabled: taskId > 0,
  })
}

/**
 * Fetch all available task statuses
 *
 * @example
 * const { data: statuses } = useTaskStatuses()
 */
export function useTaskStatuses(enabled: boolean = true) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: tasksKeys.statuses(),
    queryFn: () => adapter.tasks.getStatuses(),
    enabled,
    staleTime: Infinity, // Statuses rarely change
  })
}
