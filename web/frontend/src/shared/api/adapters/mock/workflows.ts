/**
 * Mock Workflows Adapter
 *
 * Provides in-memory mock data for workflows, simulating API behavior.
 */

import type { Workflow, WorkflowsAdapter } from '../types'

const mockWorkflows: Workflow[] = [
  {
    id: 12,
    name: 'Mineru OCR',
    tags: ['ai-inference', 'mineru-ocr'],
    createdBy: 'admin',
    eventEntity: null,
    eventType: null,
    documentTypes: [],
    entityTags: [],
    temporalWorkflowType: 'BadgerdocOCRMinerUWorkflow',
    temporalQueue: 'badgerdoc_ocr_mineru',
    isActive: true,
    trigger: 'manual',
    extractionScope: ['page'],
    supportPrompts: false,
    createdAt: '2026-03-26T09:44:09.748000Z',
    updatedAt: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 13,
    name: 'Dots OCR',
    tags: ['ai-inference', 'dots-ocr'],
    createdBy: 'admin',
    eventEntity: null,
    eventType: null,
    documentTypes: [],
    entityTags: [],
    temporalWorkflowType: 'BadgerdocOCRDotsOCRWorkflow',
    temporalQueue: 'badgerdoc_ocr_dotsocr',
    isActive: true,
    trigger: 'manual',
    extractionScope: ['page'],
    supportPrompts: false,
    createdAt: '2026-03-26T09:44:09.748000Z',
    updatedAt: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 14,
    name: 'DeepSeek OCR 2',
    tags: ['ai-inference', 'deepseek-ocr-2'],
    createdBy: 'admin',
    eventEntity: null,
    eventType: null,
    documentTypes: [],
    entityTags: [],
    temporalWorkflowType: 'BadgerdocDeepseek2Workflow',
    temporalQueue: 'badgerdoc_ocr_deepseek_2',
    isActive: true,
    trigger: 'manual',
    extractionScope: ['page'],
    supportPrompts: false,
    createdAt: '2026-03-26T09:44:09.748000Z',
    updatedAt: '2026-03-26T09:44:09.748000Z',
  },
  {
    id: 15,
    name: 'Paddle OCR',
    tags: ['ai-inference', 'paddle-ocr'],
    createdBy: 'admin',
    eventEntity: null,
    eventType: null,
    documentTypes: [],
    entityTags: [],
    temporalWorkflowType: 'BadgerdocOCRPaddleWorkflow',
    temporalQueue: 'badgerdoc_ocr_paddle',
    isActive: true,
    trigger: 'manual',
    extractionScope: ['page'],
    supportPrompts: true,
    createdAt: '2026-03-26T09:44:09.748000Z',
    updatedAt: '2026-04-06T13:53:30.897710Z',
  },
  {
    id: 11,
    name: '',
    tags: [],
    createdBy: 'admin',
    eventEntity: 'document',
    eventType: 'on_create',
    documentTypes: ['png'],
    entityTags: ['rendition'],
    temporalWorkflowType: 'BadgerdocDZIConvertWorkflow',
    temporalQueue: 'badgerdoc_convert',
    isActive: true,
    trigger: 'automatic',
    extractionScope: [],
    supportPrompts: false,
    createdAt: '2026-03-16T12:08:40.218000Z',
    updatedAt: '2026-03-16T14:35:58.493000Z',
  },
  {
    id: 10,
    name: '',
    tags: [],
    createdBy: 'admin',
    eventEntity: 'document',
    eventType: 'on_create',
    documentTypes: ['pdf'],
    entityTags: [],
    temporalWorkflowType: 'BadgerdocPNGConvertWorkflow',
    temporalQueue: 'badgerdoc_convert',
    isActive: true,
    trigger: 'automatic',
    extractionScope: [],
    supportPrompts: false,
    createdAt: '2026-03-13T11:37:47.509000Z',
    updatedAt: '2026-03-16T11:29:44.449000Z',
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
