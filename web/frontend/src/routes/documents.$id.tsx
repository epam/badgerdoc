import { createFileRoute } from '@tanstack/react-router'
import { WorkspacePage } from '@/features/workspace/page'

interface SearchParams {
  tag?: string
  taskId?: number
  extractionId?: number
  statusId?: number
}

export const Route = createFileRoute('/documents/$id')({
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return {
      tag: (search.tag as string) || undefined,
      taskId: search.taskId ? Number(search.taskId) : undefined,
      extractionId: search.extractionId ? Number(search.extractionId) : undefined,
      statusId: search.statusId ? Number(search.statusId) : undefined,
    }
  },
  component: WorkspacePage,
})
