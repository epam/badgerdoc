/**
 * Mock Tasks Adapter
 *
 * In-memory task operations with simulated delays for development/testing.
 * Includes mock data migrated from features/tasks/page.tsx
 */

import type { TasksAdapter } from '../types'
import type {
  Task,
  TaskStatus,
  TasksListParams,
  TasksListResponse,
  UpdateTaskRequest,
} from '@/shared/types/tasks'
import { STATUS_IDS } from '@/shared/types/tasks'

// Simulated delay for realistic async behavior
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

// =============================================================================
// Mock Data
// =============================================================================

const mockStatuses: TaskStatus[] = [
  { id: STATUS_IDS.NOT_PROCESSED, name: 'Not processed', order: 1 },
  { id: STATUS_IDS.DUPLICATES_CHECK, name: 'Duplicates check', order: 2 },
  { id: STATUS_IDS.CONTINUE_PROCESSING, name: 'Continue processing', order: 3 },
  { id: STATUS_IDS.READY_FOR_RELEVANCE_CHECK, name: 'Ready for relevance check', order: 4 },
  { id: STATUS_IDS.CONFIRM, name: 'Confirm', order: 5 },
  { id: STATUS_IDS.READY_FOR_CURATION, name: 'Ready for curation', order: 6 },
  { id: STATUS_IDS.FINISH_CURATION, name: 'Finish curation', order: 7 },
  { id: STATUS_IDS.CURATED, name: 'Curated', order: 8 },
  { id: STATUS_IDS.REJECT, name: 'Reject', order: 9 },
  { id: STATUS_IDS.REJECT_WITH_REASON, name: 'Reject with reason', order: 10 },
  { id: STATUS_IDS.REJECT_DUPLICATE, name: 'Reject duplicate', order: 11 },
]

// Status transitions: which statuses can follow which
const statusTransitions: Record<number, number[]> = {
  [STATUS_IDS.NOT_PROCESSED]: [STATUS_IDS.DUPLICATES_CHECK],
  [STATUS_IDS.DUPLICATES_CHECK]: [STATUS_IDS.CONTINUE_PROCESSING, STATUS_IDS.REJECT_DUPLICATE],
  [STATUS_IDS.CONTINUE_PROCESSING]: [STATUS_IDS.READY_FOR_RELEVANCE_CHECK],
  [STATUS_IDS.READY_FOR_RELEVANCE_CHECK]: [STATUS_IDS.CONFIRM, STATUS_IDS.REJECT],
  [STATUS_IDS.CONFIRM]: [STATUS_IDS.READY_FOR_CURATION],
  [STATUS_IDS.READY_FOR_CURATION]: [STATUS_IDS.FINISH_CURATION, STATUS_IDS.REJECT_WITH_REASON],
  [STATUS_IDS.FINISH_CURATION]: [STATUS_IDS.CURATED],
  [STATUS_IDS.CURATED]: [],
  [STATUS_IDS.REJECT]: [],
  [STATUS_IDS.REJECT_WITH_REASON]: [],
  [STATUS_IDS.REJECT_DUPLICATE]: [],
}

// Initial mock tasks data (migrated from features/tasks/page.tsx mockDocuments)
const initialMockTasks: Task[] = [
  {
    id: 1,
    user: 1,
    status: { id: STATUS_IDS.DUPLICATES_CHECK, name: 'Duplicates check', order: 2 },
    document: {
      id: 1,
      file: 'material_composition.pdf',
      metadata: {
        title: 'Material Composition for High-Temperature Applications',
        type: 'patent',
        authors: ['J. Smith', 'A. Johnson'],
      },
      tags: null,
    },
    extractions: [],
    created_at: '2024-12-06T15:30:00Z',
    updated_at: '2024-12-06T15:30:00Z',
  },
  {
    id: 2,
    user: 1,
    status: {
      id: STATUS_IDS.READY_FOR_RELEVANCE_CHECK,
      name: 'Ready for relevance check',
      order: 4,
    },
    document: {
      id: 2,
      file: 'composite_material.pdf',
      metadata: {
        title: 'Novel Composite Material with Enhanced Optical Properties',
        type: 'paper',
        authors: ['M. Chen'],
      },
      tags: null,
    },
    extractions: [{ id: 1, status: 'pending', comment: null, tags: [] }],
    created_at: '2024-12-06T14:00:00Z',
    updated_at: '2024-12-06T14:00:00Z',
  },
  {
    id: 3,
    user: 1,
    status: { id: STATUS_IDS.DUPLICATES_CHECK, name: 'Duplicates check', order: 2 },
    document: {
      id: 3,
      file: 'thermal_expansion.pdf',
      metadata: {
        title: 'Thermal Expansion Coefficient Optimization in Advanced Materials',
        type: 'paper',
        authors: ['R. Williams', 'S. Lee'],
      },
      tags: null,
    },
    extractions: [],
    created_at: '2024-12-05T10:00:00Z',
    updated_at: '2024-12-05T10:00:00Z',
  },
  {
    id: 4,
    user: 1,
    status: { id: STATUS_IDS.READY_FOR_CURATION, name: 'Ready for curation', order: 6 },
    document: {
      id: 4,
      file: 'advanced_material_manufacturing.pdf',
      metadata: {
        title: 'Advanced Material Manufacturing Process',
        type: 'patent',
        authors: ['K. Tanaka', 'Y. Yamamoto'],
      },
      tags: null,
    },
    extractions: [{ id: 2, status: 'complete', comment: null, tags: [] }],
    created_at: '2024-12-06T16:00:00Z',
    updated_at: '2024-12-06T16:00:00Z',
  },
  {
    id: 5,
    user: 1,
    status: { id: STATUS_IDS.CURATED, name: 'Curated', order: 8 },
    document: {
      id: 5,
      file: 'advanced_composite.pdf',
      metadata: {
        title: 'Advanced Composite for Display Applications',
        type: 'patent',
        authors: ['L. Anderson'],
      },
      tags: null,
    },
    extractions: [{ id: 3, status: 'approved', comment: null, tags: [] }],
    created_at: '2024-12-04T09:00:00Z',
    updated_at: '2024-12-04T12:00:00Z',
  },
  {
    id: 6,
    user: 1,
    status: { id: STATUS_IDS.DUPLICATES_CHECK, name: 'Duplicates check', order: 2 },
    document: {
      id: 6,
      file: 'chemically_strengthened.pdf',
      metadata: {
        title: 'Chemically Strengthened Material Composition',
        type: 'paper',
        authors: ['P. Martinez', 'Q. Brown'],
      },
      tags: null,
    },
    extractions: [],
    created_at: '2024-12-06T11:00:00Z',
    updated_at: '2024-12-06T11:00:00Z',
  },
  {
    id: 7,
    user: 1,
    status: { id: STATUS_IDS.CURATED, name: 'Curated', order: 8 },
    document: {
      id: 7,
      file: 'uv_resistant.pdf',
      metadata: {
        title: 'UV-Resistant Material for Outdoor Applications',
        type: 'patent',
        authors: ['A. Wilson'],
      },
      tags: null,
    },
    extractions: [{ id: 4, status: 'approved', comment: null, tags: [] }],
    created_at: '2024-12-03T14:00:00Z',
    updated_at: '2024-12-03T16:00:00Z',
  },
  {
    id: 8,
    user: 1,
    status: {
      id: STATUS_IDS.READY_FOR_RELEVANCE_CHECK,
      name: 'Ready for relevance check',
      order: 4,
    },
    document: {
      id: 8,
      file: 'high_index_material.pdf',
      metadata: {
        title: 'High-Index Material for Optical Fibers',
        type: 'paper',
        authors: ['T. Kim', 'J. Park'],
      },
      tags: null,
    },
    extractions: [{ id: 5, status: 'pending', comment: null, tags: [] }],
    created_at: '2024-12-06T08:00:00Z',
    updated_at: '2024-12-06T08:00:00Z',
  },
]

// In-memory store that can be mutated
const tasksStore = [...initialMockTasks]

// =============================================================================
// Mock Adapter
// =============================================================================

export const mockTasksAdapter: TasksAdapter = {
  list: async (params?: TasksListParams): Promise<TasksListResponse> => {
    await delay(300)

    let filtered = [...tasksStore]

    // Filter by status name
    if (params?.status_id) {
      filtered = filtered.filter((t) => t.status.id === params.status_id)
    }

    // Filter by user
    if (params?.user_id) {
      filtered = filtered.filter((t) => t.user === params.user_id)
    }

    // Sort by created_at descending (newest first)
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    // Pagination
    const page = params?.page || 1
    const pageSize = params?.page_size || 20
    const start = (page - 1) * pageSize
    const end = start + pageSize
    const paginated = filtered.slice(start, end)

    return {
      count: filtered.length,
      next: end < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results: paginated,
    }
  },

  getById: async (taskId: number): Promise<Task> => {
    await delay(200)
    const task = tasksStore.find((t) => t.id === taskId)
    if (!task) {
      throw new Error(`Task not found: ${taskId}`)
    }
    return task
  },

  updateStatus: async (taskId: number, request: UpdateTaskRequest): Promise<Task> => {
    await delay(300)
    const index = tasksStore.findIndex((t) => t.id === taskId)
    if (index === -1) {
      throw new Error(`Task not found: ${taskId}`)
    }

    const newStatus = mockStatuses.find((s) => s.id === request.status)
    if (!newStatus) {
      throw new Error(`Invalid status: ${request.status}`)
    }

    // Validate transition
    const currentStatusId = tasksStore[index].status.id
    const allowedTransitions = statusTransitions[currentStatusId] || []
    if (!allowedTransitions.includes(request.status)) {
      throw new Error(`Invalid status transition from ${currentStatusId} to ${request.status}`)
    }

    tasksStore[index] = {
      ...tasksStore[index],
      status: { ...newStatus },
      updated_at: new Date().toISOString(),
    }

    return tasksStore[index]
  },

  getStatuses: async (): Promise<TaskStatus[]> => {
    await delay(100)
    return [...mockStatuses]
  },

  getNextStatuses: async (currentStatusId: number): Promise<TaskStatus[]> => {
    await delay(100)
    const allowedIds = statusTransitions[currentStatusId] || []
    return mockStatuses.filter((s) => allowedIds.includes(s.id))
  },
}
