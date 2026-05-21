import type {
  Workflow,
  WorkflowsAdapter,
  WorkflowRegistryResponse,
  WorkflowTriggerResponse,
  WorkflowStatusResponse,
  WorkflowTriggerRequest,
} from '@/shared/api/adapters/types'
import { badgerDocClient } from '../../badgerdoc/client'

function toWorkflow(workflow: WorkflowRegistryResponse): Workflow {
  return {
    id: workflow.id,
    name: workflow.name ?? '',
    tags: workflow.tags ?? [],
    createdBy: workflow.created_by,
    eventEntity: workflow.event_entity || null,
    eventType: workflow.event_type || null,
    documentTypes: workflow.document_types || [],
    entityTags: workflow.entity_tags || [],
    temporalWorkflowType: workflow.temporal_workflow_type,
    temporalQueue: workflow.temporal_queue,
    isActive: !!workflow.is_active,
    trigger: workflow.trigger,
    extractionScope: workflow.extraction_scope || [],
    supportPrompts: !!workflow.support_prompts,
    createdAt: workflow.created_at,
    updatedAt: workflow.updated_at,
  }
}

export const realWorkflowsAdapter: WorkflowsAdapter = {
  list: async (params) => {
    const response = await badgerDocClient.get<WorkflowRegistryResponse[]>(`/workflow-registry`, {
      params: {
        ...params,
        tags: params?.tags?.join(','),
      },
    })
    return response.data.map(toWorkflow)
  },

  getById: async (workflowId) => {
    const response = await badgerDocClient.get<WorkflowRegistryResponse>(
      `/workflow-registry/${workflowId}/`
    )
    return toWorkflow(response.data)
  },

  trigger: async (workflowId, payload: WorkflowTriggerRequest) => {
    const response = await badgerDocClient.post<WorkflowTriggerResponse>(
      `/workflow-registry/manual-trigger/${workflowId}/`,
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
