import { createFileRoute, Outlet } from '@tanstack/react-router'
import { normalizeTaskFiltersSearch, TaskFiltersSearch } from '@/helpers/task-filters-search'

export const Route = createFileRoute('/tasks')({
  validateSearch: (search: Record<string, unknown>): TaskFiltersSearch => {
    return normalizeTaskFiltersSearch(search)
  },
  component: () => <Outlet />,
})
