import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { transformHocrToHighlights } from '@/shared/api/badgerdoc/transformers'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import {
  addBlockToExtractionPages,
  appendBlockToPageHtml,
  cleanBlockAttributes,
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

function normalizePageContent(content?: string) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(content || '', 'text/html')

  doc.querySelectorAll('[data-new]').forEach((el) => el.removeAttribute('data-new'))

  return doc.body.innerHTML
}

function arePagesEqual(a?: string, b?: string) {
  return normalizePageContent(a) === normalizePageContent(b)
}

function areExtractionPagesEquivalent(
  first?: BadgerDocExtractionPage[],
  second?: BadgerDocExtractionPage[]
) {
  if (first === second) return true
  if (!first || !second || first.length !== second.length) return false

  const secondByPage = new Map(second.map((page) => [page.page_number, page.content]))

  return first.every((page) => {
    return (
      normalizePageContent(page.content) ===
      normalizePageContent(secondByPage.get(page.page_number))
    )
  })
}

function applyAcceptedPayloadToExtractionPages({
  pages,
  payload,
}: {
  pages?: BadgerDocExtractionPage[]
  payload: PendingPayload
}) {
  if (!pages || !payload.length) return pages

  const acceptedByPage = new Map(payload.map(({ page, hocr }) => [page, hocr]))

  return pages.map((page) => {
    const acceptedContent = acceptedByPage.get(page.page_number)
    if (acceptedContent === undefined) return page

    return {
      ...page,
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

export function useExtractionState({ extractionPages, activeTag }: UseExtractionStateParams) {
  const [activeBlockId, setActiveBlockId] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pendingPages, setPendingPages] = useState<Map<number, string> | null>(null)
  const [deletedBlockIds, setDeletedBlockIds] = useState<string[]>([])
  const [stateTag, setStateTag] = useState(activeTag)
  const baselinePagesRef = useRef<Map<number, string> | null>(null)
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

  const hasChanges =
    editedExtractionPages !== undefined || pendingPages !== null || deletedBlockIds.length > 0
  const baseExtractionPages = committedExtractionPages ?? extractionPages
  const scopedExtractionPages = editedExtractionPages ?? baseExtractionPages
  const originalBlockIds = useMemo(
    () => getBlockIdsFromExtractionPages(extractionPages),
    [extractionPages]
  )

  // Keep a ref so callbacks captured by the Tiptap extension (which never
  // re-applies options) read the current value instead of a stale closure.
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

  const handleContentChange = useCallback((html: string) => {
    const currentPages = splitHtmlByPage(html)
    const baseline = baselinePagesRef.current

    if (!baseline) {
      setPendingPages(currentPages)
      return
    }

    const changed = new Map<number, string>()

    for (const [page, pageHtml] of currentPages) {
      if (baseline.get(page) !== pageHtml) {
        changed.set(page, pageHtml)
      }
    }

    // Detect pages where all blocks were removed
    for (const page of baseline.keys()) {
      if (!currentPages.has(page)) {
        changed.set(page, '')
      }
    }

    setPendingPages((prev) => {
      const next = new Map(prev ?? [])

      for (const [page, html] of changed) {
        next.set(page, html)
      }

      return next.size > 0 ? next : null
    })
  }, [])

  const handleBlockDelete = useCallback((blockId: string, pageNumber: number | null) => {
    setEditedExtractionPages((prev) => {
      const base = prev ?? baseExtractionPagesRef.current
      return removeBlockFromExtractionPages(base, blockId) ?? base
    })
    setDeletedBlockIds((prev) => [...prev, blockId])
    setActiveBlockId((prev) => (prev === blockId ? null : prev))

    if (pageNumber === null) return

    setPendingPages((prev) => {
      const pageHtml = prev?.get(pageNumber)
      if (pageHtml === undefined) return prev

      const next = new Map(prev)
      next.set(pageNumber, removeBlockFromPageHtml(pageHtml, blockId))
      return next
    })
  }, [])

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
        // Keep this defensive cleanup so restored/legacy IDs don't hide a new highlight.
        setDeletedBlockIds((prev) => prev.filter((id) => id !== newBlockId))

        let newBlockHtml: string | null = null
        const updatedPage = result.pages?.[pageIndex]
        const pageNumber = updatedPage?.page_number ?? null
        if (updatedPage?.content) {
          const parser = new DOMParser()
          const doc = parser.parseFromString(updatedPage.content, 'text/html')
          newBlockHtml = doc.getElementById(newBlockId)?.outerHTML ?? null
        }

        if (pageNumber !== null && newBlockHtml) {
          const createdPageNumber = pageNumber
          const createdBlockHtml = newBlockHtml
          const createdBlockId = newBlockId

          setPendingPages((prev) => {
            if (!prev?.has(createdPageNumber)) return prev
            const next = new Map(prev)
            next.set(
              createdPageNumber,
              appendBlockToPageHtml(
                prev.get(createdPageNumber) ?? '',
                createdBlockHtml,
                createdBlockId
              )
            )
            return next
          })
        }
      }
    },
    [baseExtractionPages, deletedBlockIds, editedExtractionPages, originalBlockIds]
  )

  const pendingPayload = useMemo(() => {
    if (!activeTag || !extractionPages?.length) return []

    const changedPages = new Map<number, string>()

    if (editedExtractionPages && scopedExtractionPages?.length) {
      const parser = new DOMParser()

      // Normalize original content to body.innerHTML for fair comparison,
      // since editedExtractionPages content is stored as body.innerHTML by mapExtractionPagesHtml
      const safePages = editedExtractionPages ?? extractionPages

      const originalByPage = new Map<number, string>(
        (extractionPages ?? []).map((p) => {
          const doc = parser.parseFromString(p.content || '', 'text/html')
          return [p.page_number, doc.body.innerHTML]
        })
      )

      for (const page of safePages ?? []) {
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
            pageTitle: getPageTitle(safePages, page.page_number),
            htmlContent: ocrPage?.innerHTML ?? updatedContent,
          })
        )
      }
    }

    if (pendingPages) {
      for (const [page, html] of pendingPages) {
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
  }, [activeTag, extractionPages, editedExtractionPages, pendingPages, scopedExtractionPages])

  const acceptChanges = useCallback(
    (acceptedPayload: PendingPayload = pendingPayload) => {
      if (!hasChanges || !activeTag || !extractionPages) return
      setCommittedExtractionPages(
        applyAcceptedPayloadToExtractionPages({
          pages: scopedExtractionPages,
          payload: acceptedPayload,
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
  }
}
