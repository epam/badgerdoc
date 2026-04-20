import { createFileRoute } from '@tanstack/react-router'
import { WorkspacePage } from '@/features/workspace/page'
import { normalizeTaskFiltersSearch, TaskFiltersSearch } from '@/helpers/task-filters-search'

interface SearchParams extends TaskFiltersSearch {
  tag?: string
}

export const Route = createFileRoute('/tasks/$taskId')({
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    const normalizedFilters = normalizeTaskFiltersSearch(search)
    const tag = typeof search.tag === 'string' && search.tag.trim() ? search.tag : undefined

    return {
      ...normalizedFilters,
      tag,
    }
  },
  component: WorkspacePage,
})
