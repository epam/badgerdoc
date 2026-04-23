import { describe, expect, it } from 'vitest'
import {
  appendPromptContextLink,
  buildBlockContextPath,
  buildDocumentContextPath,
  buildPageContextPath,
  findPromptContextLinks,
  formatPromptContextLink,
  parsePromptContextLinks,
  removePromptContextLinks,
  summarizePromptContext,
} from './extraction-chat-context'

describe('extraction chat context helpers', () => {
  it('builds exact BadgerDoc context paths', () => {
    expect(buildDocumentContextPath(123)).toBe('/badgerdoc/document/123/')
    expect(buildPageContextPath({ documentId: 123, extractionId: null, pageNumber: 1 })).toBe(
      '/badgerdoc/document/123/page/1'
    )
    expect(buildPageContextPath({ documentId: 123, extractionId: 456, pageNumber: 1 })).toBe(
      '/badgerdoc/document/123/extraction/456/page/1/'
    )
    expect(
      buildBlockContextPath({
        documentId: 123,
        extractionId: 456,
        pageNumber: 1,
        blockId: 'block_1_1',
      })
    ).toBe("/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])")
  })

  it('parses embedded context links without changing their order or removing overlaps', () => {
    const prompt = [
      formatPromptContextLink('/badgerdoc/document/123/page/1'),
      'explain',
      formatPromptContextLink('/badgerdoc/document/123/extraction/456/page/1/'),
      formatPromptContextLink(
        "/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])"
      ),
      formatPromptContextLink('/badgerdoc/document/123/page/1'),
    ].join(' ')

    const tokens = parsePromptContextLinks(prompt)

    expect(tokens.map((token) => token.raw)).toEqual([
      '{{/badgerdoc/document/123/page/1}}',
      '{{/badgerdoc/document/123/extraction/456/page/1/}}',
      "{{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}",
      '{{/badgerdoc/document/123/page/1}}',
    ])
    expect(tokens.map((token) => token.kind)).toEqual([
      'document-page',
      'extraction-page',
      'block',
      'document-page',
    ])
  })

  it('derives UI summary from the prompt without normalizing the prompt itself', () => {
    const prompt =
      "Use {{/badgerdoc/document/123/}} and {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}} plus {{/badgerdoc/document/123/extraction/456/page/1/}}"

    const summary = summarizePromptContext(prompt)

    expect(summary.hasContext).toBe(true)
    expect(summary.isWholeDocumentSelected).toBe(true)
    expect(summary.selectedPages).toEqual([1])
    expect(summary.selectedBlocks).toEqual([{ blockId: 'block_1_1', pageNumber: 1 }])
    expect(summary.primaryScope).toBe('document')
    expect(summary.primaryPage).toBeNull()
  })

  it('does not promote block links into selected page links for the UI', () => {
    const summary = summarizePromptContext(
      "Use {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}"
    )

    expect(summary.selectedPages).toEqual([])
    expect(summary.selectedBlocks).toEqual([{ blockId: 'block_1_1', pageNumber: 1 }])
    expect(summary.primaryScope).toBe('page')
    expect(summary.primaryPage).toBe(1)
  })

  it('appends links without deduplicating existing context', () => {
    const link = '/badgerdoc/document/123/page/1'
    const prompt = appendPromptContextLink(formatPromptContextLink(link), link)

    expect(prompt).toBe('{{/badgerdoc/document/123/page/1}} {{/badgerdoc/document/123/page/1}}')
  })

  it('removes matching links while preserving surrounding authored text', () => {
    const prompt =
      'Before {{/badgerdoc/document/123/page/1}} middle {{/badgerdoc/document/123/extraction/456/page/2/}} after'

    expect(removePromptContextLinks(prompt, (token) => token.pageNumber === 1)).toBe(
      'Before  middle {{/badgerdoc/document/123/extraction/456/page/2/}} after'
    )
  })

  it('does not parse escaped context syntax', () => {
    const prompt = String.raw`Keep \{{/badgerdoc/document/123/}} as text`

    expect(findPromptContextLinks(prompt)).toEqual([])
    expect(parsePromptContextLinks(prompt)).toEqual([])
  })

  it('parses arbitrary block xpath while deriving block ids when available', () => {
    const tokens = parsePromptContextLinks(
      "{{/badgerdoc/document/123/extraction/456/page/1/(//section[1])}} {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}"
    )

    expect(tokens).toMatchObject([
      { kind: 'block', blockId: undefined },
      { kind: 'block', blockId: 'block_1_1' },
    ])
  })

  it('accepts document-page paths with or without a trailing slash', () => {
    const withSlash = parsePromptContextLinks('{{/badgerdoc/document/123/page/1/}}')
    const withoutSlash = parsePromptContextLinks('{{/badgerdoc/document/123/page/1}}')

    expect(withSlash).toMatchObject([{ kind: 'document-page', pageNumber: 1 }])
    expect(withoutSlash).toMatchObject([{ kind: 'document-page', pageNumber: 1 }])
  })
})
