import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'

type ExtractionPageDocumentMapper = (
  pageDocument: Document,
  page: BadgerDocExtractionPage,
  pageIndex: number
) => void

function mapExtractionPagesHtml(
  pages: BadgerDocExtractionPage[] | undefined,
  mapper: ExtractionPageDocumentMapper
): BadgerDocExtractionPage[] | undefined {
  if (!pages?.length) {
    return pages
  }

  const parser = new DOMParser()

  return pages.map((page, pageIndex) => {
    if (!page.content) {
      return page
    }

    const pageDocument = parser.parseFromString(page.content, 'text/html')
    mapper(pageDocument, page, pageIndex)

    return {
      ...page,
      content: pageDocument.body.innerHTML,
    }
  })
}

/** Split editor HTML into a map of page number → page HTML */
export function splitHtmlByPage(html: string): Map<number, string> {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const pages = new Map<number, string>()

  doc.querySelectorAll('[data-block-id]').forEach((blockEl) => {
    const page = Number(blockEl.getAttribute('data-page'))
    if (!page) return
    const existing = pages.get(page) ?? ''
    pages.set(page, existing + blockEl.outerHTML)
  })

  return pages
}

/** Strip tiptap data-* attributes and restore original hOCR attribute names */
export function cleanBlockAttributes(html: string): string {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  doc.querySelectorAll('[data-new]').forEach((el) => el.removeAttribute('data-new'))

  doc.querySelectorAll('[data-block-id]').forEach((el) => {
    const blockId = el.getAttribute('data-block-id')
    const title = el.getAttribute('data-block-title')

    if (blockId) el.setAttribute('id', blockId)
    if (title) el.setAttribute('title', title)

    el.removeAttribute('data-block-id')
    el.removeAttribute('data-block-title')
    el.removeAttribute('data-page')
  })

  return doc.body.innerHTML
}

export function removeBlockFromPageHtml(html: string, blockId: string) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const block =
    doc.getElementById(blockId) || doc.querySelector(`[data-block-id="${CSS.escape(blockId)}"]`)

  if (block) {
    block.remove()
  }

  return doc.body.innerHTML
}

export function appendBlockToPageHtml(html: string, blockHtml: string, blockId: string) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  const existingBlock =
    doc.getElementById(blockId) || doc.querySelector(`[data-block-id="${CSS.escape(blockId)}"]`)
  if (existingBlock) {
    return doc.body.innerHTML
  }

  const blockDoc = parser.parseFromString(blockHtml, 'text/html')
  const block =
    blockDoc.getElementById(blockId) ||
    blockDoc.querySelector(`[data-block-id="${CSS.escape(blockId)}"]`)

  if (block) {
    doc.body.appendChild(doc.importNode(block, true))
  }

  return doc.body.innerHTML
}

export function removeBlockFromExtractionPages(
  pages: BadgerDocExtractionPage[] | undefined,
  blockId: string
): BadgerDocExtractionPage[] | undefined {
  return mapExtractionPagesHtml(pages, (pageDocument) => {
    const blockElement = pageDocument.getElementById(blockId)
    if (blockElement) {
      blockElement.remove()
    }
  })
}

/** Extract the ocr_page title attribute from an extraction page's content */
export function getPageTitle(
  extractionPages: BadgerDocExtractionPage[],
  pageNumber: number
): string {
  const page = extractionPages.find((p) => p.page_number === pageNumber)
  if (!page?.content) return ''

  const parser = new DOMParser()
  const doc = parser.parseFromString(page.content, 'text/html')
  return doc.querySelector('.ocr_page')?.getAttribute('title') ?? ''
}

/** Wrap page content in a full hOCR document */
export function toHOCR({
  tag,
  page,
  pageTitle,
  htmlContent,
}: {
  tag: string
  page: number
  pageTitle: string
  htmlContent: string
}) {
  return `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
  <head>
    <meta name="ocr-system" content="${tag}"/>
    <meta name="ocr-capabilities" content="ocr_page ocr_carea ocr_par ocr_line"/>
  </head>
  <body>
    <div class="ocr_page" id="page_${page}" title="${pageTitle}">
      ${htmlContent}
    </div>
  </body>
</html>`
}

interface NormalizedBBox {
  x: number
  y: number
  width: number
  height: number
}

const clampNormalized = (value: number) => Math.max(0, Math.min(1, value))

const toHocrCoordinate = (value: number) => Math.round(clampNormalized(value) * 1000)

export function updateBlockBoundingBoxInExtractionPages(
  pages: BadgerDocExtractionPage[] | undefined,
  blockId: string,
  pageIndex: number,
  bbox: NormalizedBBox
): BadgerDocExtractionPage[] | undefined {
  return mapExtractionPagesHtml(pages, (pageDocument, _page, currentPageIndex) => {
    if (currentPageIndex !== pageIndex) {
      return
    }

    const blockElement = pageDocument.getElementById(blockId)
    if (!blockElement) {
      return
    }

    const x1 = toHocrCoordinate(bbox.x)
    const y1 = toHocrCoordinate(bbox.y)
    const x2 = toHocrCoordinate(bbox.x + bbox.width)
    const y2 = toHocrCoordinate(bbox.y + bbox.height)

    const title = blockElement.getAttribute('title') || ''
    const nextBboxValue = `bbox ${x1} ${y1} ${x2} ${y2}`
    const nextTitle = title.match(/bbox \d+ \d+ \d+ \d+/)
      ? title.replace(/bbox \d+ \d+ \d+ \d+/, nextBboxValue)
      : [nextBboxValue, title].filter(Boolean).join('; ')

    blockElement.setAttribute('title', nextTitle)
  })
}

function ensurePageExists(pages: BadgerDocExtractionPage[] | undefined, targetPageNumber: number) {
  const safePages = pages ?? []

  if (!safePages.some((p) => p.page_number === targetPageNumber)) {
    return [
      ...safePages,
      {
        page_number: targetPageNumber,
        content: `<div class="ocr_page"  id="page_${targetPageNumber}" title="bbox 0 0 1000 1000"></div>`,
      },
    ].sort((a, b) => a.page_number - b.page_number)
  }

  return safePages
}

export function addBlockToExtractionPages(
  pages: BadgerDocExtractionPage[] | undefined,
  pageIndex: number,
  bbox: NormalizedBBox,
  reservedBlockIds: Iterable<string> = []
): { pages: BadgerDocExtractionPage[] | undefined; blockId: string | null } {
  let blockId: string | null = null

  const targetPageNumber = pageIndex + 1
  const safePages = ensurePageExists(pages ?? [], targetPageNumber)

  const nextPages = mapExtractionPagesHtml(safePages, (pageDocument, page) => {
    if (page.page_number !== targetPageNumber) {
      return
    }

    const pageNumber = page.page_number
    let maxIndex = 0

    const trackBlockIndex = (id: string) => {
      const match = id.match(new RegExp(`^block_${pageNumber}_(\\d+)$`))
      if (match) {
        maxIndex = Math.max(maxIndex, Number(match[1]))
      }
    }

    pageDocument.querySelectorAll(`[id^='block_${pageNumber}_']`).forEach((el) => {
      trackBlockIndex(el.id)
    })
    Array.from(reservedBlockIds).forEach(trackBlockIndex)

    blockId = `block_${pageNumber}_${maxIndex + 1}`

    const x1 = toHocrCoordinate(bbox.x)
    const y1 = toHocrCoordinate(bbox.y)
    const x2 = toHocrCoordinate(bbox.x + bbox.width)
    const y2 = toHocrCoordinate(bbox.y + bbox.height)

    const block = pageDocument.createElement('div')
    block.className = 'ocr_carea'
    block.id = blockId
    block.setAttribute('title', `bbox ${x1} ${y1} ${x2} ${y2}`)
    block.setAttribute('data-new', 'true')

    const emptyParagraph = pageDocument.createElement('p')
    emptyParagraph.appendChild(pageDocument.createTextNode('\u200B'))
    block.appendChild(emptyParagraph)

    const container = pageDocument.querySelector('.ocr_page') ?? pageDocument.body
    container.appendChild(block)
  })

  return { pages: nextPages, blockId }
}

export function formatExtractionContentForEditor(
  extractionPages?: BadgerDocExtractionPage[]
): string {
  if (!extractionPages?.length) {
    return ''
  }

  const formattedPages = mapExtractionPagesHtml(extractionPages, (pageDocument) => {
    const pageNodes = Array.from(pageDocument.body.querySelectorAll('.ocr_page'))
    if (pageNodes.length > 0) {
      pageDocument.body.innerHTML = pageNodes.map((page) => page.outerHTML).join('')
    }

    const pageId = pageDocument.querySelector('.ocr_page')?.getAttribute('id')
    const pageNumber = pageId?.match(/\d+$/)?.[0]

    if (!pageNumber) {
      return
    }

    pageDocument.querySelectorAll('.ocr_carea').forEach((careaElement) => {
      careaElement.setAttribute('data-page', pageNumber)
    })
  })

  return (
    formattedPages
      ?.sort((a, b) => a.page_number - b.page_number)
      .map((page) => page.content || '')
      .join('') || ''
  )
}
