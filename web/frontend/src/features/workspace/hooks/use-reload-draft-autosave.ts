import { useEffect, useRef } from 'react'

type ExtractionDraftPayload = Array<{ page: number; hocr: string }>

interface PersistedExtractionDraft {
  payload: ExtractionDraftPayload
  savedAt: number
}

interface UseReloadDraftAutosaveParams {
  documentId: string
  activeTagName?: string
  hasChanges: boolean
  pendingPayload: ExtractionDraftPayload
  onRestoreDraft: (payload: ExtractionDraftPayload) => Promise<unknown>
}

function getDraftStorageKey(documentId: string, activeTagName?: string) {
  return `workspace-extraction-draft:${documentId}:${activeTagName ?? 'default'}`
}

export function useReloadDraftAutosave({
  documentId,
  activeTagName,
  hasChanges,
  pendingPayload,
  onRestoreDraft,
}: UseReloadDraftAutosaveParams) {
  const hasChangesRef = useRef(hasChanges)
  const pendingPayloadRef = useRef(pendingPayload)
  const isRestoringRef = useRef(false)

  useEffect(() => {
    hasChangesRef.current = hasChanges
    pendingPayloadRef.current = pendingPayload
  }, [hasChanges, pendingPayload])

  useEffect(() => {
    if (!documentId) return

    const storageKey = getDraftStorageKey(documentId, activeTagName)

    const persistDraft = () => {
      if (!hasChangesRef.current || !pendingPayloadRef.current?.length) {
        sessionStorage.removeItem(storageKey)
        return
      }

      const draft: PersistedExtractionDraft = {
        payload: pendingPayloadRef.current,
        savedAt: Date.now(),
      }

      sessionStorage.setItem(storageKey, JSON.stringify(draft))
    }

    window.addEventListener('beforeunload', persistDraft)
    window.addEventListener('pagehide', persistDraft)

    return () => {
      window.removeEventListener('beforeunload', persistDraft)
      window.removeEventListener('pagehide', persistDraft)
      persistDraft()
    }
  }, [documentId, activeTagName])

  useEffect(() => {
    if (!documentId || isRestoringRef.current) return

    const storageKey = getDraftStorageKey(documentId, activeTagName)
    const rawDraft = sessionStorage.getItem(storageKey)
    if (!rawDraft) return

    let parsedDraft: PersistedExtractionDraft | null = null

    try {
      parsedDraft = JSON.parse(rawDraft) as PersistedExtractionDraft
    } catch {
      sessionStorage.removeItem(storageKey)
      return
    }

    if (!parsedDraft?.payload?.length) {
      sessionStorage.removeItem(storageKey)
      return
    }

    isRestoringRef.current = true

    void (async () => {
      try {
        await onRestoreDraft(parsedDraft.payload)
        sessionStorage.removeItem(storageKey)
      } catch {
        // Keep draft in sessionStorage for another retry on the next reload.
      } finally {
        isRestoringRef.current = false
      }
    })()
  }, [documentId, activeTagName, onRestoreDraft])
}
