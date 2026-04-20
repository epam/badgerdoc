import { createRootRoute, Outlet } from '@tanstack/react-router'
import { PageLayout } from '@/design-system/layouts/page-layout'
import { ErrorBoundary } from '@/components/error-boundary'
import { RouteNotFoundPage } from '@/components/not-found'

export const Route = createRootRoute({
  component: () => (
    <PageLayout>
      <ErrorBoundary>
        <Outlet />
      </ErrorBoundary>
    </PageLayout>
  ),
  notFoundComponent: RouteNotFoundPage,
})
