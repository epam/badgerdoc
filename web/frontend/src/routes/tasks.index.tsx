import { createFileRoute } from '@tanstack/react-router'
import { TasksPage } from '@/features/tasks/page'
import { normalizeTaskFiltersSearch, TaskFiltersSearch } from '@/helpers/task-filters-search'

export const Route = createFileRoute('/tasks/')({
  validateSearch: (search: Record<string, unknown>): TaskFiltersSearch => {
    return normalizeTaskFiltersSearch(search)
  },
  component: TasksPage,
})
