import { getFileExtensionFromFileName } from '@/helpers/utils'
import type { Document } from '@/shared/types/api'

function extensionFromText(value?: unknown): string {
  if (typeof value !== 'string' || !value.trim()) {
    return ''
  }

  const withoutQuery = value.trim().split(/[?#]/)[0]
  const filename = withoutQuery.split('/').filter(Boolean).pop() || withoutQuery
  const extension = getFileExtensionFromFileName(filename).replace(/^\./, '')

  if (!/^[a-z0-9]{1,6}$/i.test(extension)) {
    return ''
  }

  return extension.toUpperCase()
}

function normalizeExtension(value?: unknown): string {
  if (typeof value !== 'string') {
    return ''
  }

  const extension = value.trim().replace(/^\./, '')
  if (!/^[a-z0-9]{1,6}$/i.test(extension)) {
    return ''
  }

  return extension.toUpperCase()
}

export function getDocumentExtension(document: Document, visibleTitle?: string): string {
  const metadata = document.metadata ?? {}
  const candidates = [
    visibleTitle,
    metadata.title,
    metadata.file_name,
    metadata.filename,
    metadata.name,
    document.title,
    document.pdfUrl,
  ]

  for (const candidate of candidates) {
    const extension = extensionFromText(candidate)
    if (extension) {
      return extension
    }
  }

  return normalizeExtension(document.extension)
}
