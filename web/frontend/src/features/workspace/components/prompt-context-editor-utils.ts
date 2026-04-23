import type { Node as ProseMirrorNode } from '@tiptap/pm/model'
import type { JSONContent } from '@tiptap/react'
import {
  findPromptContextLinks,
  formatPromptContextLink,
  parsePromptContextPath,
} from '@/features/workspace/helpers/extraction-chat-context'

function createTextNode(text: string): JSONContent | null {
  return text ? { type: 'text', text } : null
}

function createInlinePromptContent(text: string): JSONContent[] {
  const content: JSONContent[] = []
  let cursor = 0

  findPromptContextLinks(text).forEach(({ raw, path, index }) => {
    const token = parsePromptContextPath(path)
    const before = createTextNode(text.slice(cursor, index))

    if (before) {
      content.push(before)
    }

    if (token) {
      content.push({
        type: 'promptContextToken',
        attrs: { path },
      })
    } else {
      content.push({ type: 'text', text: raw })
    }

    cursor = index + raw.length
  })

  const after = createTextNode(text.slice(cursor))

  if (after) {
    content.push(after)
  }

  return content
}

export function createPromptEditorContent(value: string): JSONContent {
  const lines = value.split('\n')

  return {
    type: 'doc',
    content: (lines.length ? lines : ['']).map((line) => ({
      type: 'paragraph',
      content: createInlinePromptContent(line),
    })),
  }
}

function serializeInlineNode(node: JSONContent) {
  if (node.type === 'text') {
    return node.text ?? ''
  }

  if (node.type === 'promptContextToken' && typeof node.attrs?.path === 'string') {
    return formatPromptContextLink(node.attrs.path)
  }

  return ''
}

export function serializePromptEditorContent(content: JSONContent) {
  return (content.content ?? [])
    .map((paragraph) => (paragraph.content ?? []).map(serializeInlineNode).join(''))
    .join('\n')
}

export function serializePromptEditorDoc(doc: ProseMirrorNode) {
  const paragraphs: string[] = []

  doc.forEach((paragraph) => {
    let paragraphText = ''

    paragraph.descendants((node) => {
      if (node.isText) {
        paragraphText += node.text ?? ''
        return
      }

      if (node.type.name === 'promptContextToken' && typeof node.attrs.path === 'string') {
        paragraphText += formatPromptContextLink(node.attrs.path)
        return
      }

      if (node.type.name === 'hardBreak') {
        paragraphText += '\n'
      }
    })

    paragraphs.push(paragraphText)
  })

  return paragraphs.join('\n')
}
