import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { badgerDocService } from '@/shared/api/badgerdoc'

const workflowKeys = {
  all: ['badgerdoc-workflows'] as const,
  lists: (filters?: Record<string, unknown>) => [...workflowKeys.all, 'list', filters] as const,
  item: (id?: number) => [...workflowKeys.all, 'item', id] as const,
  status: (workflowId?: string | null) => [...workflowKeys.all, 'status', workflowId] as const,
}

type WorlflowFilterParams = Parameters<typeof badgerDocService.getWorkflows>[0]

function useWorkflows(params?: WorlflowFilterParams) {
  return useQuery({
    queryKey: workflowKeys.lists(params),
    queryFn: () => badgerDocService.getWorkflows(params),
    staleTime: 1000 * 60,
  })
}

export function useChatWorkflows() {
  return useWorkflows({
    tags: ['ai-inference'],
  })
}

export function useWorkflow(id?: number) {
  return useQuery({
    queryKey: workflowKeys.item(id),
    queryFn: () => badgerDocService.getWorkflow(id ?? 0),
    enabled: !!id,
  })
}

export function useTriggerWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      badgerDocService.triggerWorkflow(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all })
    },
  })
}

export function useWorkflowStatus(
  workflowId?: string | null,
  { refetchInterval } = { refetchInterval: 3000 }
) {
  return useQuery({
    queryKey: workflowKeys.status(workflowId),
    queryFn: () => badgerDocService.getWorkflowStatus(workflowId || ''),
    enabled: !!workflowId,
    refetchInterval: workflowId ? refetchInterval : false,
  })
}
