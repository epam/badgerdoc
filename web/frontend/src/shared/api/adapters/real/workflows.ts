import type {
  WorkflowsAdapter,
  WorkflowRegistryResponse,
  WorkflowTriggerResponse,
  WorkflowStatusResponse,
  WorkflowTriggerRequest,
} from '@/shared/api/adapters/types'
import { badgerDocClient } from '../../badgerdoc/client'

export const realWorkflowsAdapter: WorkflowsAdapter = {
  list: async (params) => {
    const response = await badgerDocClient.get<WorkflowRegistryResponse[]>(`/workflow-registry`, {
      params: {
        ...params,
        tags: params?.tags?.join(','),
      },
    })
    return response.data
  },

  getById: async (workflowId) => {
    const response = await badgerDocClient.get<WorkflowRegistryResponse>(
      `/workflow-registry/${workflowId}/`
    )
    return response.data
  },

  trigger: async (workflowId, payload: WorkflowTriggerRequest) => {
    const response = await badgerDocClient.post<WorkflowTriggerResponse>(
      `/workflow-registry/trigger/${workflowId}/`,
      payload
    )
    return response.data
  },

  getStatus: async (workflowId) => {
    const response = await badgerDocClient.get<WorkflowStatusResponse>(
      `/workflow-registry/workflow/status/${workflowId}/`
    )
    return response.data
  },
}
