import { delay } from 'msw'
import type { AgentLogsAdapter } from '@/shared/api/adapters/types'
import type { AgentLog } from '@/shared/api/badgerdoc/types'

const PAGE_SIZE = 20

const mockAgentLogs: AgentLog[] = [
  {
    id: 1,
    document: 1,
    task: null,
    level: 'INFO',
    source: 'Django',
    log: { message: 'Workflow request accepted' },
    created_at: '2026-05-18T09:00:00Z',
  },
  {
    id: 2,
    document: 1,
    task: null,
    level: 'INFO',
    source: 'Temporal',
    log: { message: 'Preparing document context' },
    created_at: '2026-05-18T09:00:05Z',
  },
  {
    id: 3,
    document: 1,
    task: null,
    level: 'INFO',
    source: 'Temporal',
    log: { markdown: 'Loaded **document** and selected context.' },
    created_at: '2026-05-18T09:00:10Z',
  },
  {
    id: 4,
    document: 1,
    task: null,
    level: 'WARNING',
    source: 'Temporal',
    log: { message: 'Some extraction blocks were unavailable and skipped' },
    created_at: '2026-05-18T09:00:15Z',
  },
]

function getPageUrl(page: number, hasPage: boolean) {
  return hasPage ? `?page=${page}` : null
}

export const mockAgentLogsAdapter: AgentLogsAdapter = {
  getAgentLogs: async ({ after, page = 1 }) => {
    await delay(200)

    const filteredLogs = after
      ? mockAgentLogs.filter((log) => log.created_at >= after)
      : mockAgentLogs
    const sortedLogs = [...filteredLogs].sort((left, right) =>
      right.created_at.localeCompare(left.created_at)
    )
    const start = (page - 1) * PAGE_SIZE
    const end = start + PAGE_SIZE
    const results = sortedLogs.slice(start, end)

    return {
      count: sortedLogs.length,
      next: getPageUrl(page + 1, end < sortedLogs.length),
      previous: getPageUrl(page - 1, page > 1),
      results,
    }
  },
}
