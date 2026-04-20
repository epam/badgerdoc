import { useQuery } from '@tanstack/react-query'
import { duplicateCheckAdapter } from '@/shared/api/adapters/duplicate-check'

const duplicateCheckKeys = {
  all: ['duplicate-check'] as const,
  decisions: () => [...duplicateCheckKeys.all, 'decisions'] as const,
  decision: (documentId: string) => [...duplicateCheckKeys.all, 'decision', documentId] as const,
  similarDocument: (documentId: string) =>
    [...duplicateCheckKeys.all, 'similar', documentId] as const,
}

/**
 * Hook to get all duplicate check decisions
 */
export function useDuplicateDecisions() {
  return useQuery({
    queryKey: duplicateCheckKeys.decisions(),
    queryFn: () => duplicateCheckAdapter.getAllDecisions(),
    staleTime: Infinity, // Decisions don't change unless we mutate them
  })
}
