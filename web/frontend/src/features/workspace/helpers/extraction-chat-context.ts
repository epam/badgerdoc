export interface ExtractionContextBlock {
  blockId: string
  pageNumber: number
}

export type PromptContextPathInserter = (path: string) => void
export type PromptContextPathInserterRegistration = (
  inserter: PromptContextPathInserter | null
) => void

export interface PromptContextToken {
  raw: string
  path: string
  kind: 'document' | 'document-page' | 'extraction-page' | 'block'
  documentId: number
  extractionId?: number
  pageNumber?: number
  blockId?: string
}

export interface PromptContextLinkMatch {
  raw: string
  path: string
  index: number
}

export interface PromptContextSummary {
  tokens: PromptContextToken[]
  hasContext: boolean
  isWholeDocumentSelected: boolean
  selectedPages: number[]
  selectedBlocks: ExtractionContextBlock[]
  primaryScope: 'document' | 'page' | null
  primaryPage: number | null
}

export const BADGERDOC_CONTEXT_LINK_PATTERN =
  /(?<!\\)\{\{(\/badgerdoc\/document\/\d+\/(?:page\/\d+\/?|extraction\/\d+\/page\/\d+\/(?:\([^{}]+\))?)?)\}\}/g

const DOCUMENT_PATH_PATTERN = /^\/badgerdoc\/document\/(\d+)\/$/
const DOCUMENT_PAGE_PATH_PATTERN = /^\/badgerdoc\/document\/(\d+)\/page\/(\d+)\/?$/
const EXTRACTION_PAGE_PATH_PATTERN =
  /^\/badgerdoc\/document\/(\d+)\/extraction\/(\d+)\/page\/(\d+)\/$/
const EXTRACTION_BLOCK_PATH_PATTERN =
  /^\/badgerdoc\/document\/(\d+)\/extraction\/(\d+)\/page\/(\d+)\/\((.+)\)$/
const BLOCK_ID_XPATH_PATTERN = /^\/\/div\[@id='([^']+)'\]$/

function numberFromMatch(value: string) {
  return Number(value)
}

export function parsePromptContextPath(path: string): PromptContextToken | null {
  const documentMatch = path.match(DOCUMENT_PATH_PATTERN)
  if (documentMatch) {
    return {
      raw: formatPromptContextLink(path),
      path,
      kind: 'document',
      documentId: numberFromMatch(documentMatch[1]),
    }
  }

  const documentPageMatch = path.match(DOCUMENT_PAGE_PATH_PATTERN)
  if (documentPageMatch) {
    return {
      raw: formatPromptContextLink(path),
      path,
      kind: 'document-page',
      documentId: numberFromMatch(documentPageMatch[1]),
      pageNumber: numberFromMatch(documentPageMatch[2]),
    }
  }

  const extractionPageMatch = path.match(EXTRACTION_PAGE_PATH_PATTERN)
  if (extractionPageMatch) {
    return {
      raw: formatPromptContextLink(path),
      path,
      kind: 'extraction-page',
      documentId: numberFromMatch(extractionPageMatch[1]),
      extractionId: numberFromMatch(extractionPageMatch[2]),
      pageNumber: numberFromMatch(extractionPageMatch[3]),
    }
  }

  const extractionBlockMatch = path.match(EXTRACTION_BLOCK_PATH_PATTERN)
  if (extractionBlockMatch) {
    const blockId = extractionBlockMatch[4].match(BLOCK_ID_XPATH_PATTERN)?.[1]

    return {
      raw: formatPromptContextLink(path),
      path,
      kind: 'block',
      documentId: numberFromMatch(extractionBlockMatch[1]),
      extractionId: numberFromMatch(extractionBlockMatch[2]),
      pageNumber: numberFromMatch(extractionBlockMatch[3]),
      blockId,
    }
  }

  return null
}

export function findPromptContextLinks(text: string): PromptContextLinkMatch[] {
  BADGERDOC_CONTEXT_LINK_PATTERN.lastIndex = 0

  return Array.from(text.matchAll(BADGERDOC_CONTEXT_LINK_PATTERN)).map((match) => ({
    raw: match[0],
    path: match[1],
    index: match.index ?? 0,
  }))
}

export function parsePromptContextLinks(prompt: string): PromptContextToken[] {
  return findPromptContextLinks(prompt)
    .map((match) => parsePromptContextPath(match.path))
    .filter((token): token is PromptContextToken => token !== null)
}

function uniqueSortedNumbers(values: number[]) {
  return [...new Set(values)].sort((left, right) => left - right)
}

function uniqueSortedBlocks(blocks: ExtractionContextBlock[]) {
  const next = new Map<string, ExtractionContextBlock>()

  blocks.forEach((block) => {
    next.set(block.blockId, block)
  })

  return [...next.values()].sort((left, right) => {
    if (left.pageNumber !== right.pageNumber) {
      return left.pageNumber - right.pageNumber
    }

    return left.blockId.localeCompare(right.blockId)
  })
}

export function summarizePromptContext(prompt: string): PromptContextSummary {
  const tokens = parsePromptContextLinks(prompt)
  const selectedPages = uniqueSortedNumbers(
    tokens.flatMap((token) =>
      (token.kind === 'document-page' || token.kind === 'extraction-page') && token.pageNumber
        ? [token.pageNumber]
        : []
    )
  )
  const selectedBlocks = uniqueSortedBlocks(
    tokens.flatMap((token) =>
      token.kind === 'block' && token.blockId && token.pageNumber
        ? [{ blockId: token.blockId, pageNumber: token.pageNumber }]
        : []
    )
  )
  const firstContextToken = tokens[0]

  return {
    tokens,
    hasContext: tokens.length > 0,
    isWholeDocumentSelected: tokens.some((token) => token.kind === 'document'),
    selectedPages,
    selectedBlocks,
    primaryScope: firstContextToken
      ? firstContextToken.kind === 'document'
        ? 'document'
        : 'page'
      : null,
    primaryPage: firstContextToken?.pageNumber ?? null,
  }
}

export function buildDocumentContextPath(documentId: string | number) {
  return `/badgerdoc/document/${documentId}/`
}

export function buildPageContextPath({
  documentId,
  extractionId,
  pageNumber,
}: {
  documentId: string | number
  extractionId: number | null
  pageNumber: number
}) {
  if (extractionId !== null) {
    return `/badgerdoc/document/${documentId}/extraction/${extractionId}/page/${pageNumber}/`
  }

  return `/badgerdoc/document/${documentId}/page/${pageNumber}`
}

export function buildBlockContextPath({
  documentId,
  extractionId,
  pageNumber,
  blockId,
}: {
  documentId: string | number
  extractionId: number | null
  pageNumber: number
  blockId: string
}) {
  if (extractionId === null) {
    return null
  }

  return `/badgerdoc/document/${documentId}/extraction/${extractionId}/page/${pageNumber}/(//div[@id='${blockId}'])`
}

export function formatPromptContextLink(path: string) {
  return `{{${path}}}`
}

export function appendPromptContextLink(prompt: string, path: string) {
  const link = formatPromptContextLink(path)

  if (!prompt) {
    return link
  }

  return /\s$/.test(prompt) ? `${prompt}${link}` : `${prompt} ${link}`
}

export function removePromptContextLinks(
  prompt: string,
  predicate: (token: PromptContextToken) => boolean
) {
  return prompt.replace(BADGERDOC_CONTEXT_LINK_PATTERN, (raw, path: string) => {
    const token = parsePromptContextPath(path)

    return token && predicate(token) ? '' : raw
  })
}

export function getContextBlockLabel(blockId: string) {
  const match = blockId.match(/^block_(\d+)_(.+)$/)
  if (!match) {
    return 'Block (unknown)'
  }

  return `Block ${match[1]}.${match[2]}`
}

export interface ExtractionChatContextProps {
  prompt: string
  isWholeDocumentSelected: boolean
  selectedPages: number[]
  selectedBlocks: ExtractionContextBlock[]
  onPromptChange: (prompt: string) => void
  registerPromptContextInserter: PromptContextPathInserterRegistration
  onAddWholeDocument: () => void
  onAddCurrentPage: () => void
  onToggleBlock: (blockId: string, pageNumber: number | null) => void
}
