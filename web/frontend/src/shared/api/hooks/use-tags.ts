import { useQuery } from '@tanstack/react-query'
import { getApiAdapter } from '@/shared/api/adapters/factory.ts'

const tagsKeys = {
  all: ['badgerdoc-tags'] as const,
}

export function useTags() {
  return useQuery({
    queryKey: tagsKeys.all,
    queryFn: () => getApiAdapter().tags.getTags(),
    staleTime: Infinity, // Tags rarely change
  })
}
