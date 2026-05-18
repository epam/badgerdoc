/**
 * BadgerDoc API Module
 *
 * Exports for BadgerDoc API integration.
 */

// Client

// Service
export { badgerDocService } from './service'

// Types
export type {
  AgentLog,
  AgentLogLevel,
  AgentLogPayload,
  AgentLogsResponse,
  BadgerDocExtractionPage,
  BadgerDocExtraction,
  GetAgentLogsParams,
} from './types'

// Transformers
export { transformBadgerDocDocument } from './transformers'
