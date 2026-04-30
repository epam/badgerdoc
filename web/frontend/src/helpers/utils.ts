import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Re-export color utilities from centralized theme config
export { getConfidenceColor, getStatusColor } from '@/shared/config/theme'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function formatTimeAgo(date: string | Date): string {
  const now = new Date()
  const then = new Date(date)
  const diffMs = now.getTime() - then.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return then.toLocaleDateString()
}

/**
 * Extract filename from a URL path
 *
 * Handles MinIO URLs like:
 * http://minio:9000/badgerdoc/documents/abc123/pdf_1.pdf?AWSAccessKeyId=...
 * Returns: pdf_1.pdf
 *
 * Also handles simple paths like:
 * /path/to/file.pdf -> file.pdf
 * file.pdf -> file.pdf
 */
export function extractFilenameFromUrl(urlOrPath: string): string {
  if (!urlOrPath) return ''

  try {
    // Try to parse as URL first
    const url = new URL(urlOrPath, 'http://localhost')
    const pathname = url.pathname

    // Get the last segment of the path
    const segments = pathname.split('/').filter(Boolean)
    return segments[segments.length - 1] || urlOrPath
  } catch {
    // If URL parsing fails, treat as simple path
    const segments = urlOrPath.split('/').filter(Boolean)
    return segments[segments.length - 1] || urlOrPath
  }
}

/**
 * Extracts the file extension from a filename.
 *
 * The extension is defined as the substring after the last "." character
 * in the filename. If the filename does not contain an extension,
 * the function returns an empty string.
 *
 * Examples:
 * - "document.pdf" -> "pdf"
 * - "archive.tar.gz" -> "gz"
 * - "README" -> ""
 *
 * @param {string} fileName - The name of the file
 * @returns {string} - The file extension in lowercase, or an empty string if none exists
 */
export function getFileExtensionFromFileName(fileName: string): string {
  const index = fileName.lastIndexOf('.')
  if (index === -1) return ''
  return fileName.slice(index + 1).toLowerCase()
}

export function parsePositiveNumber(value: unknown): number | null {
  const numericValue =
    typeof value === 'number' ? value : typeof value === 'string' ? Number(value) : null

  if (numericValue == null || !Number.isFinite(numericValue) || numericValue <= 0) {
    return null
  }

  return numericValue
}
