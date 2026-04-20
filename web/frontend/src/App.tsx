import { useEffect, type ReactNode } from 'react'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query'
import { Toaster, toast } from 'sonner'
import { routeTree } from './routeTree.gen'
import { useUIStore } from '@/shared/hooks/use-ui-store'
import { ErrorBoundary } from '@/components/error-boundary'
import { APIError } from '@/shared/api/client'
import { logger } from '@/shared/logger'

// Global error handler for queries
function handleQueryError(error: unknown) {
  // APIError already shows toast via interceptor, skip duplicates
  if (error instanceof APIError) return

  // Handle unexpected errors
  logger.error('Query error:', error)
  toast.error('Failed to load data', {
    description: error instanceof Error ? error.message : 'Please try again.',
  })
}

// Global error handler for mutations
function handleMutationError(error: unknown) {
  // APIError already shows toast via interceptor, skip duplicates
  if (error instanceof APIError) return

  logger.error('Mutation error:', error)
  toast.error('Operation failed', {
    description: error instanceof Error ? error.message : 'Please try again.',
  })
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleQueryError,
  }),
  mutationCache: new MutationCache({
    onError: handleMutationError,
  }),
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (garbage collection)
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
})

const router = createRouter({
  routeTree,
  basepath: '/ui',
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

function ThemeProvider({ children }: { children: ReactNode }) {
  const { theme } = useUIStore()

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }, [theme])

  useEffect(() => {
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        const root = window.document.documentElement
        root.classList.remove('light', 'dark')
        root.classList.add(mediaQuery.matches ? 'dark' : 'light')
      }
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  return <>{children}</>
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RouterProvider router={router} />
          <Toaster
            position="bottom-right"
            richColors
            closeButton
            toastOptions={{
              duration: 5000,
              classNames: {
                actionButton:
                  '!bg-[var(--success-text)] !text-white !border-none hover:!opacity-90 rounded-md px-4 py-2 transition-all',
              },
            }}
          />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
