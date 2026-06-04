import { describe, expect, it } from 'vitest'
import type { AgentLog } from '@/shared/api/badgerdoc/types'
import {
  dedupeAgentLogs,
  mergeAgentLogs,
  normalizeAgentLogsPage,
  normalizeAgentLogsResponse,
} from './use-agent-logs'

function createAgentLog(id: number | string, createdAt: string): AgentLog {
  return {
    id,
    document: 123,
    task: null,
    level: 'INFO',
    source: 'Temporal',
    log: { message: `Log ${id}` },
    created_at: createdAt,
  }
}

describe('agent log helpers', () => {
  it('normalizes a backend page from newest-first to oldest-first', () => {
    const logs = [
      createAgentLog(3, '2026-05-18T10:02:00Z'),
      createAgentLog(2, '2026-05-18T10:01:00Z'),
      createAgentLog(1, '2026-05-18T10:00:00Z'),
    ]

    expect(normalizeAgentLogsPage(logs).map((log) => log.id)).toEqual([1, 2, 3])
  })

  it('keeps equal-timestamp logs in their original relative order', () => {
    const logs = [
      createAgentLog('first', '2026-05-18T10:00:00Z'),
      createAgentLog('second', '2026-05-18T10:00:00Z'),
      createAgentLog('third', '2026-05-18T10:00:00Z'),
    ]

    expect(normalizeAgentLogsPage(logs).map((log) => log.id)).toEqual([
      'first',
      'second',
      'third',
    ])
  })

  it('dedupes logs by id and keeps timeline order', () => {
    const logs = [
      createAgentLog(2, '2026-05-18T10:01:00Z'),
      createAgentLog(1, '2026-05-18T10:00:00Z'),
      createAgentLog('2', '2026-05-18T10:01:00Z'),
      createAgentLog(3, '2026-05-18T10:02:00Z'),
    ]

    expect(dedupeAgentLogs(logs).map((log) => log.id)).toEqual([1, 2, 3])
  })

  it('merges inclusive polling results without duplicating the latest existing log', () => {
    const existingLogs = [
      createAgentLog(1, '2026-05-18T10:00:00Z'),
      createAgentLog(2, '2026-05-18T10:01:00Z'),
    ]
    const incomingLogs = [
      createAgentLog(2, '2026-05-18T10:01:00Z'),
      createAgentLog(3, '2026-05-18T10:02:00Z'),
    ]

    expect(mergeAgentLogs(existingLogs, incomingLogs).map((log) => log.id)).toEqual([1, 2, 3])
  })

  it('normalizes response results while preserving pagination metadata', () => {
    const response = {
      count: 2,
      next: '?page=2',
      previous: null,
      results: [
        createAgentLog(2, '2026-05-18T10:01:00Z'),
        createAgentLog(1, '2026-05-18T10:00:00Z'),
      ],
    }

    expect(normalizeAgentLogsResponse(response)).toEqual({
      ...response,
      results: [response.results[1], response.results[0]],
    })
  })
})
