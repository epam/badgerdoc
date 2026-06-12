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

export function hasMeaningfulWorkflowParams(value: unknown, seen = new WeakSet<object>()): boolean {
  if (value === null || value === undefined) {
    return false
  }

  if (typeof value === 'string') {
    return value.trim().length > 0
  }

  if (Array.isArray(value)) {
    if (seen.has(value)) {
      return true
    }
    seen.add(value)

    return value.some((item) => hasMeaningfulWorkflowParams(item, seen))
  }

  if (typeof value === 'object') {
    if (seen.has(value)) {
      return true
    }
    seen.add(value)

    return Object.values(value).some((item) => hasMeaningfulWorkflowParams(item, seen))
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

export function getWorkflowHeaderLabel(workflowParams: unknown) {
  if (
    typeof workflowParams !== 'object' ||
    workflowParams === null ||
    Array.isArray(workflowParams)
  ) {
    return null
  }

  const workflow = (workflowParams as Record<string, unknown>).workflow
  if (typeof workflow !== 'object' || workflow === null || Array.isArray(workflow)) {
    return null
  }

  const workflowRecord = workflow as Record<string, unknown>
  const name = typeof workflowRecord.name === 'string' ? workflowRecord.name.trim() : ''
  const trigger = typeof workflowRecord.trigger === 'string' ? workflowRecord.trigger.trim() : ''

  if (!name) {
    return null
  }

  return trigger ? `${name} · ${trigger}` : name
}
