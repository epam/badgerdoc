import { useQuery } from '@tanstack/react-query'
import { getApiAdapter } from '@/shared/api/adapters/factory'
import type { AgentLog, AgentLogsResponse, GetAgentLogsParams } from '@/shared/api/badgerdoc/types'

export const agentLogsKeys = {
  all: ['badgerdoc-agent-logs'] as const,
  document: (documentId: string | number) => [...agentLogsKeys.all, String(documentId)] as const,
  list: (params: GetAgentLogsParams) =>
    [
      ...agentLogsKeys.document(params.documentId),
      {
        after: params.after,
        page: params.page ?? 1,
      },
    ] as const,
}

function getCreatedAtTime(log: AgentLog) {
  const time = Date.parse(log.created_at)
  return Number.isFinite(time) ? time : null
}

function compareAgentLogsByCreatedAt(
  left: AgentLog,
  right: AgentLog,
  leftIndex: number,
  rightIndex: number
) {
  const leftTime = getCreatedAtTime(left)
  const rightTime = getCreatedAtTime(right)

  if (leftTime !== null && rightTime !== null && leftTime !== rightTime) {
    return leftTime - rightTime
  }

  if (left.created_at !== right.created_at) {
    return left.created_at.localeCompare(right.created_at)
  }

  return leftIndex - rightIndex
}

export function normalizeAgentLogsPage(logs: AgentLog[]): AgentLog[] {
  return logs
    .map((log, index) => ({ log, index }))
    .sort((left, right) =>
      compareAgentLogsByCreatedAt(left.log, right.log, left.index, right.index)
    )
    .map(({ log }) => log)
}

export function dedupeAgentLogs(logs: AgentLog[]): AgentLog[] {
  const logsById = new Map<string, AgentLog>()

  for (const log of logs) {
    const id = String(log.id)
    if (!logsById.has(id)) {
      logsById.set(id, log)
    }
  }

  return normalizeAgentLogsPage([...logsById.values()])
}

export function mergeAgentLogs(existingLogs: AgentLog[], incomingLogs: AgentLog[]): AgentLog[] {
  return dedupeAgentLogs([...existingLogs, ...incomingLogs])
}

export function normalizeAgentLogsResponse(response: AgentLogsResponse): AgentLogsResponse {
  return {
    ...response,
    results: normalizeAgentLogsPage(response.results),
  }
}

export async function fetchAgentLogs(params: GetAgentLogsParams) {
  return normalizeAgentLogsResponse(await getApiAdapter().agentLogs.getAgentLogs(params))
}

export function useAgentLogs(params: GetAgentLogsParams, enabled = true) {
  return useQuery({
    queryKey: agentLogsKeys.list(params),
    queryFn: () => fetchAgentLogs(params),
    enabled: Boolean(params.documentId) && enabled,
    refetchOnWindowFocus: false,
  })
}
