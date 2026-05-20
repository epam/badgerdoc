import type { AgentLogsAdapter } from '@/shared/api/adapters/types'
import { badgerDocClient } from '@/shared/api/badgerdoc/client'
import type { AgentLogsResponse } from '@/shared/api/badgerdoc/types'

export const realAgentLogsAdapter: AgentLogsAdapter = {
  getAgentLogs: async ({ documentId, after, page }) => {
    const response = await badgerDocClient.get<AgentLogsResponse>('/agent-log/', {
      params: {
        document_id: documentId,
        ...(after ? { after } : {}),
        ...(page ? { page } : {}),
      },
    })
    return response.data
  },
}
