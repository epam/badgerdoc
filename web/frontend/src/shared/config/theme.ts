/**
 * Centralized Theme Configuration
 *
 * Single source of truth for color configurations, quality levels, and status styles.
 * Import from here instead of defining inline in components.
 */

import type { ConfidenceLevel } from '@/shared/types/api'

// =============================================================================
// Confidence Level Configuration
// =============================================================================

interface ConfidenceColorConfig {
  text: string
  bg: string
  label: string
}

const confidenceColors: Record<ConfidenceLevel, ConfidenceColorConfig> = {
  High: {
    text: 'text-mint-readable',
    bg: 'bg-mint-readable',
    label: 'High',
  },
  Medium: {
    text: 'text-foreground',
    bg: 'bg-foreground',
    label: 'Medium',
  },
  Low: {
    text: 'text-muted-foreground',
    bg: 'bg-muted-foreground',
    label: 'Low',
  },
}

/**
 * Get color configuration for a confidence level
 */
export function getConfidenceColor(confidence: ConfidenceLevel): ConfidenceColorConfig {
  return confidenceColors[confidence]
}

// =============================================================================
// Document Status Configuration
// =============================================================================

interface StatusColorConfig {
  bg: string
  text: string
  border: string
  label: string
  action: string
}

const statusColors: Record<string, StatusColorConfig> = {
  // Task statuses from backend
  new_task: {
    bg: 'bg-sky/15',
    text: 'text-sky-readable',
    border: 'border-l-sky',
    label: 'New Task',
    action: 'Review',
  },
  in_progress: {
    bg: 'bg-amber-500/15',
    text: 'text-amber-600',
    border: 'border-l-amber-500',
    label: 'In Progress',
    action: 'Validate',
  },
  cancelled: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-l-muted-foreground',
    label: 'Cancelled',
    action: 'View',
  },
  // Legacy statuses
  pending_review: {
    bg: 'bg-sky/15',
    text: 'text-sky-readable',
    border: 'border-l-sky',
    label: 'Pending Review',
    action: 'Review',
  },
  pending_analysis: {
    bg: 'bg-sky/15',
    text: 'text-sky-readable',
    border: 'border-l-sky',
    label: 'Pending Analysis',
    action: 'Review',
  },
  analysis_ready: {
    bg: 'bg-sky/15',
    text: 'text-sky-readable',
    border: 'border-l-sky',
    label: 'Analysis Ready',
    action: 'Review',
  },
  analysis_approved: {
    bg: 'bg-mint/15',
    text: 'text-mint-readable',
    border: 'border-l-mint',
    label: 'Analysis Approved',
    action: 'View',
  },
  approved: {
    bg: 'bg-mint/15',
    text: 'text-mint-readable',
    border: 'border-l-mint',
    label: 'Approved',
    action: 'View',
  },
  declined: {
    bg: 'bg-destructive/15',
    text: 'text-destructive',
    border: 'border-l-destructive',
    label: 'Declined',
    action: 'View',
  },
  analysis_rejected: {
    bg: 'bg-destructive/15',
    text: 'text-destructive',
    border: 'border-l-destructive',
    label: 'Analysis Rejected',
    action: 'View',
  },
  pending_extraction: {
    bg: 'bg-sea/15',
    text: 'text-sea-readable',
    border: 'border-l-sea',
    label: 'In Extraction',
    action: 'Validate',
  },
  extraction_ready: {
    bg: 'bg-sea/15',
    text: 'text-sea-readable',
    border: 'border-l-sea',
    label: 'Extraction Ready',
    action: 'Validate',
  },
  extraction_complete: {
    bg: 'bg-lilac/15',
    text: 'text-lilac-readable',
    border: 'border-l-lilac',
    label: 'Awaiting Approval',
    action: 'Approve',
  },
  extraction_approved: {
    bg: 'bg-mint/15',
    text: 'text-mint-readable',
    border: 'border-l-mint',
    label: 'Extraction Approved',
    action: 'View',
  },
  final_approved: {
    bg: 'bg-mint/20',
    text: 'text-mint-readable',
    border: 'border-l-mint',
    label: 'Completed',
    action: 'View',
  },
  completed: {
    bg: 'bg-mint/20',
    text: 'text-mint-readable',
    border: 'border-l-mint',
    label: 'Completed',
    action: 'View',
  },
}

/**
 * Get color configuration for a document status
 */
export function getStatusColor(status: string): StatusColorConfig {
  return statusColors[status] || statusColors.pending_review
}
