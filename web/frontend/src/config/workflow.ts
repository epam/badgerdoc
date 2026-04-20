/**
 * Workflow Configuration
 *
 * Centralized configuration for task status mappings, tab navigation,
 * and status grouping. Edit this file to adjust workflow behavior.
 *
 * Status IDs from API (/badgerdoc/task/status/):
 * - 7: Not processed
 * - 8: Duplicates check
 * - 9: Continue processing
 * - 10: Ready for relevance check
 * - 11: Confirm
 * - 12: Ready for curation
 * - 13: Finish curation
 * - 14: Curated
 * - 15: Reject duplicate
 * - 16: Reject
 * - 17: Reject with reason
 */

// =============================================================================
// STATUS IDS
// Known task status IDs from the backend. Update when backend changes.
// =============================================================================

export const STATUS_IDS = {
  // Processing statuses (intermediate/background states)
  NOT_PROCESSED: 7,
  CONTINUE_PROCESSING: 9,
  CONFIRM: 11,
  FINISH_CURATION: 13,

  // Main workflow statuses
  DUPLICATES_CHECK: 8,
  READY_FOR_RELEVANCE_CHECK: 10,
  READY_FOR_CURATION: 12,
  CURATED: 14,

  // Rejection statuses
  REJECT_DUPLICATE: 15,
  REJECT: 16,
  REJECT_WITH_REASON: 17,
} as const
