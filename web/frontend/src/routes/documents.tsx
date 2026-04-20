import { createFileRoute, Outlet } from '@tanstack/react-router'

interface DocumentsSearchParams {
  tag?: string
}

export const Route = createFileRoute('/documents')({
  validateSearch: (search: Record<string, unknown>): DocumentsSearchParams => {
    return {
      tag: (search.tag as string) || undefined,
    }
  },
  component: () => <Outlet />,
})
