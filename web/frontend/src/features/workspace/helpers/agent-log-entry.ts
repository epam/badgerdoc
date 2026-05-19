export function formatLogTime(createdAt: string) {
  const date = new Date(createdAt)
  if (Number.isNaN(date.getTime())) {
    return createdAt
  }

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function safeStringify(value: unknown) {
  const seen = new WeakSet<object>()

  try {
    return JSON.stringify(
      value,
      (_key, nestedValue) => {
        if (typeof nestedValue === 'object' && nestedValue !== null) {
          if (seen.has(nestedValue)) {
            return '[Circular]'
          }
          seen.add(nestedValue)
        }
        return nestedValue
      },
      2
    )
  } catch {
    return String(value)
  }
}

export function hasMeaningfulWorkflowParams(value: unknown) {
  if (value === null || value === undefined) {
    return false
  }

  if (typeof value === 'string') {
    return value.trim().length > 0
  }

  if (Array.isArray(value)) {
    return value.length > 0
  }

  if (typeof value === 'object') {
    return Object.keys(value).length > 0
  }

  return true
}

export function shouldShowSourceDocumentLink({
  currentDocumentId,
  sourceDocumentId,
}: {
  currentDocumentId?: number | string | null
  sourceDocumentId: number | string
}) {
  if (currentDocumentId === null || currentDocumentId === undefined) {
    return false
  }

  return String(sourceDocumentId) !== String(currentDocumentId)
}
