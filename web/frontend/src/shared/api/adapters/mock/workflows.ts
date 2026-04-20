/**
 * Mock Workflows Adapter
 *
 * Provides in-memory mock data for workflows, simulating API behavior.
 */

import type { WorkflowsAdapter, WorkflowRegistryResponse } from '../types'

const mockWorkflows: WorkflowRegistryResponse[] = [
  {
    id: 12,
    name: 'Mineru OCR',
    created_by: 'admin',
    event_entity: null,
    event_type: null,
    document_types: [],
    entity_tags: [],
    tags: ['ai-inference', 'mineru-ocr'],
    temporal_workflow_type: 'BadgerdocOCRMinerUWorkflow',
    temporal_queue: 'badgerdoc_ocr_mineru',
    is_active: true,
    trigger: 'manual',
    extraction_scope: ['page'],
    support_prompts: false,
    created_at: '2026-03-26T09:44:09.748000Z',
    updated_at: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 13,
    name: 'Dots OCR',
    created_by: 'admin',
    event_entity: null,
    event_type: null,
    document_types: [],
    entity_tags: [],
    tags: ['ai-inference', 'dots-ocr'],
    temporal_workflow_type: 'BadgerdocOCRDotsOCRWorkflow',
    temporal_queue: 'badgerdoc_ocr_dotsocr',
    is_active: true,
    trigger: 'manual',
    extraction_scope: ['page'],
    support_prompts: false,
    created_at: '2026-03-26T09:44:09.748000Z',
    updated_at: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 14,
    name: 'DeepSeek OCR 2',
    created_by: 'admin',
    event_entity: null,
    event_type: null,
    document_types: [],
    entity_tags: [],
    tags: ['ai-inference', 'deepseek-ocr-2'],
    temporal_workflow_type: 'BadgerdocDeepseek2Workflow',
    temporal_queue: 'badgerdoc_ocr_deepseek_2',
    is_active: true,
    trigger: 'manual',
    extraction_scope: ['page'],
    support_prompts: false,
    created_at: '2026-03-26T09:44:09.748000Z',
    updated_at: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 15,
    name: 'Paddle OCR',
    created_by: 'admin',
    event_entity: null,
    event_type: null,
    document_types: [],
    entity_tags: [],
    tags: ['ai-inference', 'paddle-ocr'],
    temporal_workflow_type: 'BadgerdocOCRPaddleWorkflow',
    temporal_queue: 'badgerdoc_ocr_paddle',
    is_active: true,
    trigger: 'manual',
    extraction_scope: ['page'],
    support_prompts: true,
    created_at: '2026-03-26T09:44:09.748000Z',
    updated_at: '2026-04-06T13:53:30.897710Z',
  },
  {
    id: 11,
    name: null,
    created_by: 'admin',
    event_entity: 'document',
    event_type: 'on_create',
    document_types: ['png'],
    entity_tags: ['rendition'],
    tags: [],
    temporal_workflow_type: 'BadgerdocDZIConvertWorkflow',
    temporal_queue: 'badgerdoc_convert',
    is_active: true,
    trigger: 'automatic',
    extraction_scope: [],
    support_prompts: false,
    created_at: '2026-03-16T12:08:40.218000Z',
    updated_at: '2026-03-16T14:35:58.493000Z',
  },
  {
    id: 10,
    name: null,
    created_by: 'admin',
    event_entity: 'document',
    event_type: 'on_create',
    document_types: ['pdf'],
    entity_tags: [],
    tags: [],
    temporal_workflow_type: 'BadgerdocPNGConvertWorkflow',
    temporal_queue: 'badgerdoc_convert',
    is_active: true,
    trigger: 'automatic',
    extraction_scope: [],
    support_prompts: false,
    created_at: '2026-03-13T11:37:47.509000Z',
    updated_at: '2026-03-16T11:29:44.449000Z',
  },
]

export const mockWorkflowsAdapter: WorkflowsAdapter = {
  list: async () => {
    return mockWorkflows
  },

  getById: async (workflowId) => {
    const workflow = mockWorkflows.find((w) => w.id === workflowId)
    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`)
    }
    return workflow
  },

  trigger: async (workflowId) => {
    const workflow = mockWorkflows.find((w) => w.id === workflowId)
    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`)
    }
    return { workflow_id: `mock-${workflowId}` }
  },

  getStatus: async () => {
    return { status: 'Finished' }
  },
}
