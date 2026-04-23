import { describe, expect, it } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { PromptContextToken } from './prompt-context-editor'
import {
  createPromptEditorContent,
  serializePromptEditorDoc,
  serializePromptEditorContent,
} from './prompt-context-editor-utils'

describe('prompt context editor serialization', () => {
  it('turns valid context links into token nodes', () => {
    const content = createPromptEditorContent(
      "Summarize {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}"
    )

    expect(content).toEqual({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            { type: 'text', text: 'Summarize ' },
            {
              type: 'promptContextToken',
              attrs: {
                path: "/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])",
              },
            },
          ],
        },
      ],
    })
  })

  it('serializes token nodes back to exact link syntax', () => {
    const prompt =
      'First {{/badgerdoc/document/123/}} then\n{{/badgerdoc/document/123/extraction/456/page/1/}}'

    expect(serializePromptEditorContent(createPromptEditorContent(prompt))).toBe(prompt)
  })

  it('leaves invalid braced paths as editable text', () => {
    const prompt = 'Keep {{/badgerdoc/document/123/page/not-a-number}} literal'

    expect(createPromptEditorContent(prompt)).toEqual({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [{ type: 'text', text: prompt }],
        },
      ],
    })
  })

  it('leaves escaped context syntax as editable text', () => {
    const prompt = String.raw`Keep \{{/badgerdoc/document/123/}} literal`

    expect(createPromptEditorContent(prompt)).toEqual({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [{ type: 'text', text: prompt }],
        },
      ],
    })
  })

  it('converts typed context links into atom token nodes after closing braces', () => {
    const prompt = '{{/badgerdoc/document/123/page/1}}'
    const editor = new Editor({
      extensions: [
        StarterKit.configure({
          heading: false,
          blockquote: false,
          codeBlock: false,
          bulletList: false,
          orderedList: false,
          listItem: false,
          horizontalRule: false,
        }),
        PromptContextToken,
      ],
      content: createPromptEditorContent(''),
    })

    editor.commands.insertContent(prompt)

    expect(editor.getJSON()).toMatchObject({
      content: [
        {
          content: [
            {
              type: 'promptContextToken',
              attrs: { path: '/badgerdoc/document/123/page/1' },
            },
          ],
        },
      ],
    })
    expect(serializePromptEditorDoc(editor.state.doc)).toBe(prompt)

    editor.destroy()
  })
})
