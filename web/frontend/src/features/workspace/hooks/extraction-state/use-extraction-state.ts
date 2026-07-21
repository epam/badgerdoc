import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { transformHocrToHighlights } from '@/shared/api/badgerdoc/transformers'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  addBlockToExtractionPages,
  appendBlockToPageHtml,
  cleanBlockAttributes,
  editorPageContentMatchesSaved,
  formatExtractionContentForEditor,
  getPageTitle,
  removeBlockFromExtractionPages,
  removeBlockFromPageHtml,
  splitHtmlByPage,
  toHOCR,
  updateBlockBoundingBoxInExtractionPages,
} from '@/features/workspace/helpers/extraction-utils'
import { isHighlightValid } from '@/components/collection-viewer/highlight-utils'

interface BBox {
  x: number
  y: number
  width: number
  height: number
}

interface UseExtractionStateParams {
  extractionPages?: BadgerDocExtractionPage[]
  activeTag?: string
}

type PendingPayload = Array<{ page: number; hocr: string }>
type PageHtmlMap = Map<number, string>

/**
 * Tracks in-progress extraction edits for the workspace editor.
 *
 * Unsaved changes come from three sources:
 * - pendingPages: text edits in the Tiptap editor
 * - editedExtractionPages: structural edits (block create / bbox move)
 * - deletedBlockIds: original blocks removed in this session
 *
 * Two HTML snapshots are used when deciding whether text is dirty:
 * - savedEditorPages: ground truth from the server (extractionPages)
 * - baselinePagesRef: last editor snapshot from onBaselineReady; drifts during
 *   the session and may already include in-progress text before a block create
 */

// --- Session baseline (editor HTML vs editor HTML) --------------------------------

function normalizePageContent(content?: string) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(content || '', 'text/html')

  doc.querySelectorAll('[data-new]').forEach((el) => el.removeAttribute('data-new'))

  return doc.body.innerHTML
}

function arePagesEqual(a?: string, b?: string) {
  return normalizePageContent(a) === normalizePageContent(b)
}

function sessionPagesMatch(left?: string, right?: string): boolean {
  return right !== undefined && arePagesEqual(left, right)
}

// --- hOCR page list helpers -----------------------------------------------------

function areExtractionPagesEquivalent(
  first?: BadgerDocExtractionPage[],
  second?: BadgerDocExtractionPage[]
) {
  if (first === second) return true
  if (!first || !second || first.length !== second.length) return false

  const secondByPage = new Map(second.map((page) => [page.page_number, page.content]))

  return first.every((page) => {
    return arePagesEqual(page.content, secondByPage.get(page.page_number))
  })
}

function applyAcceptedPayloadToExtractionPages({
  pages,
  payload,
  extractionId,
}: {
  pages?: BadgerDocExtractionPage[]
  payload: PendingPayload
  extractionId?: string | number | null
}) {
  if (!pages || !payload.length) return pages

  const acceptedByPage = new Map(payload.map(({ page, hocr }) => [page, hocr]))
  const acceptedExtractionId =
    extractionId === undefined || extractionId === null ? null : Number(extractionId)

  return pages.map((page) => {
    const acceptedContent = acceptedByPage.get(page.page_number)
    if (acceptedContent === undefined) return page

    return {
      ...page,
      ...(acceptedExtractionId !== null ? { extraction_id: acceptedExtractionId } : {}),
      content: acceptedContent,
    }
  })
}

function getBlockIdsFromExtractionPages(pages?: BadgerDocExtractionPage[]) {
  const parser = new DOMParser()
  const blockIds = new Set<string>()

  pages?.forEach((page) => {
    const doc = parser.parseFromString(page.content || '', 'text/html')
    doc.querySelectorAll('.ocr_carea[id]').forEach((block) => {
      blockIds.add(block.getAttribute('id')!)
    })
  })

  return blockIds
}

// --- Pending text state (editor vs session baseline / saved extraction) ---------

function collectPagesChangedFromBaseline(
  currentPages: PageHtmlMap,
  baseline: PageHtmlMap
): PageHtmlMap {
  const changed = new Map<number, string>()

  for (const [page, pageHtml] of currentPages) {
    if (!arePagesEqual(baseline.get(page), pageHtml)) {
      changed.set(page, pageHtml)
    }
  }

  for (const page of baseline.keys()) {
    if (!currentPages.has(page)) {
      changed.set(page, '')
    }
  }

  return changed
}

/** Drop stale pending entries after a revert-to-baseline within the session. */
function reconcilePendingWithSessionBaseline(
  pending: PageHtmlMap,
  baseline: PageHtmlMap | null,
  currentPages?: PageHtmlMap
): PageHtmlMap | null {
  const next = new Map(pending)

  for (const page of [...next.keys()]) {
    const pendingHtml = next.get(page)!
    const baselineHtml = baseline?.get(page)
    const currentHtml = currentPages?.get(page)

    if (currentPages) {
      if (sessionPagesMatch(currentHtml, baselineHtml)) {
        next.delete(page)
        continue
      }

      if (currentHtml === undefined && !baseline?.has(page)) {
        next.delete(page)
        continue
      }
    }

    if (sessionPagesMatch(pendingHtml, baselineHtml)) {
      next.delete(page)
    }
  }

  return next.size > 0 ? next : null
}

function removeCreatedBlockFromBaseline(
  baseline: PageHtmlMap,
  pageNumber: number,
  blockId: string
): PageHtmlMap {
  const updated = new Map(baseline)
  updated.set(pageNumber, removeBlockFromPageHtml(baseline.get(pageNumber) ?? '', blockId))
  return updated
}

// --- Saved extraction comparison (editor HTML vs server) ------------------------

function dropPendingPagesMatchingSaved(pending: PageHtmlMap, savedPages: PageHtmlMap): void {
  for (const page of [...pending.keys()]) {
    if (editorPageContentMatchesSaved(pending.get(page), savedPages.get(page))) {
      pending.delete(page)
    }
  }
}

function dropPendingWhereEditorMatchesSaved(
  pending: PageHtmlMap,
  currentPages: PageHtmlMap,
  savedPages: PageHtmlMap
): void {
  for (const [page, currentHtml] of currentPages) {
    if (editorPageContentMatchesSaved(currentHtml, savedPages.get(page))) {
      pending.delete(page)
    }
  }
}

function alignSessionBaselineToSavedWhereEditorMatches(
  baseline: PageHtmlMap,
  currentPages: PageHtmlMap,
  savedPages: PageHtmlMap
): PageHtmlMap {
  const aligned = new Map(baseline)

  for (const [page, currentHtml] of currentPages) {
    const savedHtml = savedPages.get(page)
    if (savedHtml !== undefined && editorPageContentMatchesSaved(currentHtml, savedHtml)) {
      aligned.set(page, savedHtml)
    }
  }

  return aligned
}

function editorMatchesSavedExtraction(currentPages: PageHtmlMap, savedPages: PageHtmlMap) {
  if (savedPages.size === 0) {
    return currentPages.size === 0
  }

  for (const [page, savedHtml] of savedPages) {
    if (!editorPageContentMatchesSaved(currentPages.get(page), savedHtml)) {
      return false
    }
  }

  for (const page of currentPages.keys()) {
    if (!savedPages.has(page)) {
      return false
    }
  }

  return true
}

function mergeAndReconcilePendingPages({
  prev,
  changed,
  baseline,
  currentPages,
  savedPages,
}: {
  prev: PageHtmlMap | null
  changed: PageHtmlMap
  baseline: PageHtmlMap
  currentPages: PageHtmlMap
  savedPages: PageHtmlMap
}): PageHtmlMap | null {
  const next = new Map(prev ?? [])

  for (const [page, pageHtml] of changed) {
    next.set(page, pageHtml)
  }

  const reconciled = reconcilePendingWithSessionBaseline(next, baseline, currentPages)
  const final = new Map(reconciled ?? [])
  dropPendingWhereEditorMatchesSaved(final, currentPages, savedPages)
  return final.size > 0 ? final : null
}

// --- Structural edit session (create / delete blocks) ---------------------------

function hasNoStructuralEdits(
  isCreatedBlock: boolean,
  remainingCreatedBlockIds: Set<string>,
  deletedBlockIds: string[]
) {
  return isCreatedBlock && remainingCreatedBlockIds.size === 0 && deletedBlockIds.length === 0
}

function hasStructuralEdits(
  createdBlockIds: Set<string>,
  deletedBlockIds: string[],
  originalBlockIds: Set<string>
) {
  return (
    createdBlockIds.size > 0 || deletedBlockIds.some((blockId) => originalBlockIds.has(blockId))
  )
}

export function useExtractionState({ extractionPages, activeTag }: UseExtractionStateParams) {
  const [activeBlockId, setActiveBlockId] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pendingPages, setPendingPages] = useState<PageHtmlMap | null>(null)
  const [deletedBlockIds, setDeletedBlockIds] = useState<string[]>([])
  const [stateTag, setStateTag] = useState(activeTag)
  const baselinePagesRef = useRef<PageHtmlMap | null>(null)
  const [editedExtractionPages, setEditedExtractionPages] = useState<
    BadgerDocExtractionPage[] | undefined
  >(undefined)
  const [committedExtractionPages, setCommittedExtractionPages] = useState<
    BadgerDocExtractionPage[] | undefined
  >(undefined)
  const [createdBlockIds, setCreatedBlockIds] = useState<Set<string>>(new Set())

  if (activeTag !== stateTag) {
    setStateTag(activeTag)
    setEditedExtractionPages(undefined)
    setCreatedBlockIds(new Set())
    setPendingPages(null)
    setDeletedBlockIds([])
    setCommittedExtractionPages(undefined)
    setActiveBlockId(null)
  }

  const resetEditState = useCallback(() => {
    setEditedExtractionPages(undefined)
    setCreatedBlockIds(new Set())
    setPendingPages(null)
    setDeletedBlockIds([])
  }, [])

  const savedEditorPages = useMemo(
    () => splitHtmlByPage(formatExtractionContentForEditor(extractionPages)),
    [extractionPages]
  )

  const baseExtractionPages = committedExtractionPages ?? extractionPages
  const scopedExtractionPages = editedExtractionPages ?? baseExtractionPages
  const originalBlockIds = useMemo(
    () => getBlockIdsFromExtractionPages(extractionPages),
    [extractionPages]
  )

  const baseExtractionPagesRef = useRef(baseExtractionPages)
  useEffect(() => {
    baseExtractionPagesRef.current = baseExtractionPages
  })

  useEffect(() => {
    if (
      !committedExtractionPages ||
      editedExtractionPages ||
      pendingPages ||
      deletedBlockIds.length > 0
    ) {
      return
    }

    if (!areExtractionPagesEquivalent(extractionPages, committedExtractionPages)) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      setCommittedExtractionPages(undefined)
    }, 0)

    return () => window.clearTimeout(timeoutId)
  }, [
    committedExtractionPages,
    deletedBlockIds.length,
    editedExtractionPages,
    extractionPages,
    pendingPages,
  ])

  const highlights = useMemo(() => {
    if (!scopedExtractionPages?.length) return {}

    const all = transformHocrToHighlights(scopedExtractionPages)
    if (!deletedBlockIds.length) return all

    const deletedSet = new Set(deletedBlockIds)
    const filtered: typeof all = {}
    for (const [page, boxes] of Object.entries(all)) {
      const remaining = boxes.filter((b) => !deletedSet.has(b.id))
      if (remaining.length) filtered[Number(page)] = remaining
    }
    return filtered
  }, [scopedExtractionPages, deletedBlockIds])

  const invalidBlockIds = useMemo(() => {
    const ids = new Set<string>()
    for (const pageHighlights of Object.values(highlights)) {
      for (const h of pageHighlights) {
        if (!isHighlightValid(h)) ids.add(h.id)
      }
    }
    return ids
  }, [highlights])

  const handleBaselineReady = useCallback((html: string) => {
    baselinePagesRef.current = splitHtmlByPage(html)
  }, [])

  const handleContentChange = useCallback(
    (html: string) => {
      const currentPages = splitHtmlByPage(html)
      let baseline = baselinePagesRef.current

      if (!baseline) {
        setPendingPages(currentPages)
        return
      }

      // Editor fully matches the server — clear text edits unless blocks were
      // created or original blocks were deleted in this session.
      if (
        !hasStructuralEdits(createdBlockIds, deletedBlockIds, originalBlockIds) &&
        editorMatchesSavedExtraction(currentPages, savedEditorPages)
      ) {
        baselinePagesRef.current = new Map(savedEditorPages)
        setPendingPages(null)
        return
      }

      baseline = alignSessionBaselineToSavedWhereEditorMatches(
        baseline,
        currentPages,
        savedEditorPages
      )
      baselinePagesRef.current = baseline

      const changed = collectPagesChangedFromBaseline(currentPages, baseline)

      setPendingPages((prev) =>
        mergeAndReconcilePendingPages({
          prev,
          changed,
          baseline,
          currentPages,
          savedPages: savedEditorPages,
        })
      )
    },
    [createdBlockIds, deletedBlockIds, originalBlockIds, savedEditorPages]
  )

  const handleBlockDelete = useCallback(
    (blockId: string, pageNumber: number | null) => {
      const isCreatedBlock = createdBlockIds.has(blockId)
      const remainingCreatedBlockIds = new Set(createdBlockIds)
      if (isCreatedBlock) {
        remainingCreatedBlockIds.delete(blockId)
      }

      const noStructuralEdits = hasNoStructuralEdits(
        isCreatedBlock,
        remainingCreatedBlockIds,
        deletedBlockIds
      )

      if (noStructuralEdits) {
        setEditedExtractionPages(undefined)
      } else {
        setEditedExtractionPages((prev) => {
          const base = prev ?? baseExtractionPagesRef.current
          const next = removeBlockFromExtractionPages(base, blockId) ?? base
          return areExtractionPagesEquivalent(next, extractionPages) ? undefined : next
        })
      }

      if (isCreatedBlock) {
        setCreatedBlockIds(remainingCreatedBlockIds)
      } else {
        setDeletedBlockIds((prev) => [...prev, blockId])
      }

      setActiveBlockId((prev) => (prev === blockId ? null : prev))

      if (pageNumber === null) return

      setPendingPages((prev) => {
        let baseline = baselinePagesRef.current

        if (isCreatedBlock && baseline?.has(pageNumber)) {
          baseline = removeCreatedBlockFromBaseline(baseline, pageNumber, blockId)
          baselinePagesRef.current = baseline
        }

        const next = new Map(prev ?? [])

        if (next.has(pageNumber)) {
          next.set(pageNumber, removeBlockFromPageHtml(next.get(pageNumber) ?? '', blockId))
        }

        if (noStructuralEdits) {
          // Compare against saved extraction only — the session baseline may
          // already include in-progress text edits from before the block was created.
          dropPendingPagesMatchingSaved(next, savedEditorPages)
          return next.size > 0 ? next : null
        }

        return reconcilePendingWithSessionBaseline(next, baseline)
      })
    },
    [createdBlockIds, deletedBlockIds, extractionPages, savedEditorPages]
  )

  const handleBlockBoundingBoxUpdate = useCallback(
    (blockId: string, pageIndex: number, bbox: BBox) => {
      setEditedExtractionPages((prev) => {
        const base = prev ?? baseExtractionPagesRef.current
        return updateBlockBoundingBoxInExtractionPages(base, blockId, pageIndex, bbox) ?? base
      })
    },
    []
  )

  const handleBlockCreate = useCallback(
    (pageIndex: number, bbox: BBox) => {
      const base = editedExtractionPages ?? baseExtractionPages
      const reservedBlockIds = new Set([...originalBlockIds, ...deletedBlockIds])
      const result = addBlockToExtractionPages(base, pageIndex, bbox, reservedBlockIds)
      const newBlockId = result.blockId

      setEditedExtractionPages(result.pages ?? base)

      if (newBlockId) {
        setActiveBlockId(newBlockId)
        setCreatedBlockIds((prev) => new Set(prev).add(newBlockId!))
        setDeletedBlockIds((prev) => prev.filter((id) => id !== newBlockId))

        const updatedPage = result.pages?.[pageIndex]
        const pageNumber = updatedPage?.page_number ?? null
        let newBlockHtml: string | null = null

        if (updatedPage?.content) {
          const parser = new DOMParser()
          const doc = parser.parseFromString(updatedPage.content, 'text/html')
          newBlockHtml = doc.getElementById(newBlockId)?.outerHTML ?? null
        }

        if (pageNumber !== null && newBlockHtml) {
          setPendingPages((prev) => {
            if (!prev?.has(pageNumber)) return prev
            const next = new Map(prev)
            next.set(
              pageNumber,
              appendBlockToPageHtml(prev.get(pageNumber) ?? '', newBlockHtml, newBlockId)
            )
            return next
          })
        }
      }
    },
    [baseExtractionPages, deletedBlockIds, editedExtractionPages, originalBlockIds]
  )

  const pendingPayload = useMemo(() => {
    if (!activeTag) return []

    const changedPages = new Map<number, string>()

    if (editedExtractionPages && scopedExtractionPages?.length) {
      const parser = new DOMParser()
      const originalByPage = new Map<number, string>(
        (extractionPages ?? []).map((p) => {
          const doc = parser.parseFromString(p.content || '', 'text/html')
          return [p.page_number, doc.body.innerHTML]
        })
      )

      for (const page of editedExtractionPages) {
        const originalContent = originalByPage.get(page.page_number) ?? ''
        const updatedContent = page.content || ''
        if (arePagesEqual(originalContent, updatedContent)) continue

        const doc = parser.parseFromString(updatedContent, 'text/html')
        const ocrPage = doc.querySelector('.ocr_page')

        changedPages.set(
          page.page_number,
          toHOCR({
            tag: activeTag,
            page: page.page_number,
            pageTitle: getPageTitle(editedExtractionPages, page.page_number),
            htmlContent: ocrPage?.innerHTML ?? updatedContent,
          })
        )
      }
    }

    if (pendingPages) {
      for (const [page, html] of pendingPages) {
        const savedHtml = savedEditorPages.get(page) ?? ''
        if (editorPageContentMatchesSaved(html, savedHtml)) continue

        changedPages.set(
          page,
          toHOCR({
            tag: activeTag,
            page,
            pageTitle: getPageTitle(scopedExtractionPages ?? extractionPages ?? [], page),
            htmlContent: cleanBlockAttributes(html),
          })
        )
      }
    }

    return Array.from(changedPages.entries())
      .sort(([a], [b]) => a - b)
      .map(([page, hocr]) => ({ page, hocr }))
  }, [
    activeTag,
    extractionPages,
    editedExtractionPages,
    savedEditorPages,
    pendingPages,
    scopedExtractionPages,
  ])

  const hasChanges =
    pendingPayload.length > 0 || deletedBlockIds.some((blockId) => originalBlockIds.has(blockId))

  const acceptChanges = useCallback(
    (
      acceptedPayload: PendingPayload = pendingPayload,
      acceptedExtractionId?: string | number | null
    ) => {
      if (!hasChanges || !activeTag || !extractionPages) return
      setCommittedExtractionPages(
        applyAcceptedPayloadToExtractionPages({
          pages: scopedExtractionPages,
          payload: acceptedPayload,
          extractionId: acceptedExtractionId,
        })
      )
      resetEditState()
    },
    [activeTag, extractionPages, hasChanges, pendingPayload, resetEditState, scopedExtractionPages]
  )

  const discardInvalidBlocks = useCallback(() => {
    if (invalidBlockIds.size === 0) return

    setEditedExtractionPages((prev) => {
      let pages = prev ?? baseExtractionPages
      for (const blockId of invalidBlockIds) {
        pages = removeBlockFromExtractionPages(pages, blockId) ?? pages
      }
      return pages
    })
    setDeletedBlockIds((prev) => [...prev, ...invalidBlockIds])
    setCreatedBlockIds((prev) => {
      const next = new Set(prev)
      for (const id of invalidBlockIds) next.delete(id)
      return next
    })
    setActiveBlockId((prev) => (prev && invalidBlockIds.has(prev) ? null : prev))
  }, [baseExtractionPages, invalidBlockIds])

  return {
    currentPage,
    setCurrentPage,
    activeBlockId,
    setActiveBlockId,
    hasChanges,
    scopedExtractionPages,
    highlights,
    pendingPayload,
    onBaselineReady: handleBaselineReady,
    onContentChange: handleContentChange,
    onBlockDelete: handleBlockDelete,
    revertChanges: resetEditState,
    acceptChanges,
    handleBlockBoundingBoxUpdate,
    handleBlockCreate,
    discardInvalidBlocks,
    invalidBlockIds,
    createdBlockIds,
    deletedBlockIds,
  }
}
