import type { AgentLogsAdapter } from '@/shared/api/adapters/types'
import { badgerDocService } from '@/shared/api/badgerdoc'

export const realAgentLogsAdapter: AgentLogsAdapter = {
  getAgentLogs: (params) => badgerDocService.getAgentLogs(params),
}
