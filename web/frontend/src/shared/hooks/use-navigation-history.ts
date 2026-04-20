import { useCallback, useEffect, useState } from 'react'
import { useRouter } from '@tanstack/react-router'

interface UseNavigationHistoryOptions {
  fallbackPath?: string
  fallbackSearch?: Record<string, unknown>
}

interface UseNavigationHistoryReturn {
  canGoBack: boolean
  goBack: () => void
  fallbackPath: string
}

/**
 * Smart back navigation hook that uses browser history when available,
 * falling back to a default path when there's no history.
 */
export function useNavigationHistory(
  options: UseNavigationHistoryOptions = {}
): UseNavigationHistoryReturn {
  const { fallbackPath = '/tasks', fallbackSearch } = options
  const router = useRouter()
  const [canGoBack, setCanGoBack] = useState(() => window.history.length > 1)

  useEffect(() => {
    const updateCanGoBack = () => {
      setCanGoBack(window.history.length > 1)
    }

    window.addEventListener('popstate', updateCanGoBack)
    return () => window.removeEventListener('popstate', updateCanGoBack)
  }, [])

  const goBack = useCallback(() => {
    const hasHistory = window.history.length > 1
    setCanGoBack(hasHistory)

    if (hasHistory) {
      window.history.back()
    } else {
      router.navigate({ to: fallbackPath, search: fallbackSearch })
    }
  }, [fallbackPath, fallbackSearch, router])

  return {
    canGoBack,
    goBack,
    fallbackPath,
  }
}
