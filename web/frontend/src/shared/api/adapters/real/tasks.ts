/**
 * Real Tasks Adapter
 *
 * Fetches task data from BadgerDoc API.
 *
 * Endpoints:
 * - GET /tasks/           → list()
 * - GET /task/{id}/details/ → getById()
 * - PATCH /task/{id}/     → updateStatus()
 * - GET /task/status/     → getStatuses()
 * - GET /task/status/next/{id}/ → getNextStatuses()
 */

import type { TasksAdapter } from '../types'
import type {
  Task,
  TaskStatus,
  TasksListParams,
  TasksListResponse,
  UpdateTaskRequest,
} from '@/shared/types/tasks'
import { badgerDocClient } from '../../badgerdoc/client'

export const realTasksAdapter: TasksAdapter = {
  /**
   * List tasks with optional filtering
   */
  list: async (params?: TasksListParams): Promise<TasksListResponse> => {
    const response = await badgerDocClient.get<TasksListResponse>('/tasks/', { params })
    return response.data
  },

  /**
   * Get task details by ID
   */
  getById: async (taskId: number): Promise<Task> => {
    const response = await badgerDocClient.get<Task>(`/task/${taskId}/details/`)
    return response.data
  },

  /**
   * Update task status
   */
  updateStatus: async (taskId: number, request: UpdateTaskRequest): Promise<Task> => {
    const response = await badgerDocClient.patch<Task>(`/task/${taskId}/`, request)
    return response.data
  },

  /**
   * Get all available task statuses
   */
  getStatuses: async (): Promise<TaskStatus[]> => {
    const response = await badgerDocClient.get<TaskStatus[]>('/task/status/')
    return response.data
  },

  /**
   * Get next possible statuses for a task with the given current status
   */
  getNextStatuses: async (currentStatusId: number): Promise<TaskStatus[]> => {
    const response = await badgerDocClient.get<TaskStatus[]>(
      `/task/status/next/${currentStatusId}/`
    )
    return response.data
  },
}
