import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getApiAdapter } from '@/shared/api/adapters/factory'
import type { WorkflowsAdapter } from '@/shared/api/adapters/types'

const workflowKeys = {
  all: ['badgerdoc-workflows'] as const,
  lists: (filters?: Record<string, unknown>) => [...workflowKeys.all, 'list', filters] as const,
  item: (id?: number) => [...workflowKeys.all, 'item', id] as const,
  status: (workflowId?: string | null) => [...workflowKeys.all, 'status', workflowId] as const,
}

type WorlflowFilterParams = Parameters<WorkflowsAdapter['list']>[0]

function useWorkflows(params?: WorlflowFilterParams) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workflowKeys.lists(params),
    queryFn: () => adapter.workflows.list(params),
    staleTime: 1000 * 60,
  })
}

export function useChatWorkflows() {
  return useWorkflows({
    tags: ['ai-inference'],
  })
}

export function useWorkflow(id?: number) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workflowKeys.item(id),
    queryFn: () => adapter.workflows.getById(id ?? 0),
    enabled: !!id,
  })
}

export function useTriggerWorkflow() {
  const qc = useQueryClient()
  const adapter = getApiAdapter()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      adapter.workflows.trigger(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all })
    },
  })
}

export function useWorkflowStatus(
  workflowId?: string | null,
  { refetchInterval } = { refetchInterval: 3000 }
) {
  const adapter = getApiAdapter()

  return useQuery({
    queryKey: workflowKeys.status(workflowId),
    queryFn: () => adapter.workflows.getStatus(workflowId || ''),
    enabled: !!workflowId,
    refetchInterval: workflowId ? refetchInterval : false,
  })
}
