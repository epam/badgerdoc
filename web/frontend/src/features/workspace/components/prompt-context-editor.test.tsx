import { act, fireEvent, render, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { useState } from 'react'
import { PromptContextToken } from './prompt-context-editor'
import { PromptContextEditor } from './prompt-context-editor'
import {
  createPromptEditorContent,
  serializePromptEditorDoc,
  serializePromptEditorContent,
} from './prompt-context-editor-utils'
import type { PromptContextPathInserter } from '@/features/workspace/helpers/extraction-chat-context'

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

  it('submits with Cmd+Enter on macOS when enabled', async () => {
    const originalPlatform = navigator.platform
    const onSubmitShortcut = vi.fn()

    Object.defineProperty(navigator, 'platform', {
      configurable: true,
      value: 'MacIntel',
    })

    try {
      const { container } = render(
        <PromptContextEditor
          value="Summarize"
          onChange={vi.fn()}
          canSubmit
          onSubmitShortcut={onSubmitShortcut}
        />
      )

      await waitFor(() => {
        expect(container.querySelector('.ProseMirror')).not.toBeNull()
      })

      fireEvent.keyDown(container.querySelector('.ProseMirror')!, {
        key: 'Enter',
        metaKey: true,
      })

      expect(onSubmitShortcut).toHaveBeenCalledTimes(1)
    } finally {
      Object.defineProperty(navigator, 'platform', {
        configurable: true,
        value: originalPlatform,
      })
    }
  })

  it('does not submit with Cmd+Enter when submit is disabled', async () => {
    const originalPlatform = navigator.platform
    const onSubmitShortcut = vi.fn()

    Object.defineProperty(navigator, 'platform', {
      configurable: true,
      value: 'MacIntel',
    })

    try {
      const { container } = render(
        <PromptContextEditor
          value="Summarize"
          onChange={vi.fn()}
          canSubmit={false}
          onSubmitShortcut={onSubmitShortcut}
        />
      )

      await waitFor(() => {
        expect(container.querySelector('.ProseMirror')).not.toBeNull()
      })

      fireEvent.keyDown(container.querySelector('.ProseMirror')!, {
        key: 'Enter',
        metaKey: true,
      })

      expect(onSubmitShortcut).not.toHaveBeenCalled()
    } finally {
      Object.defineProperty(navigator, 'platform', {
        configurable: true,
        value: originalPlatform,
      })
    }
  })

  it('inserts a context chip at the current cursor position', async () => {
    let promptContextInserter: PromptContextPathInserter | null = null
    let latestValue = 'Hello world'

    function TestEditor() {
      const [value, setValue] = useState(latestValue)

      return (
        <PromptContextEditor
          value={value}
          onChange={(nextValue) => {
            latestValue = nextValue
            setValue(nextValue)
          }}
          onRegisterContextInserter={(inserter) => {
            promptContextInserter = inserter
          }}
        />
      )
    }

    const { container } = render(<TestEditor />)

    await waitFor(() => {
      expect(container.querySelector('.ProseMirror')).not.toBeNull()
      expect(promptContextInserter).not.toBeNull()
    })

    const paragraphTextNode = container.querySelector('.ProseMirror p')?.firstChild
    expect(paragraphTextNode).not.toBeNull()

    const selection = window.getSelection()
    const range = document.createRange()
    range.setStart(paragraphTextNode!, 6)
    range.collapse(true)
    selection?.removeAllRanges()
    selection?.addRange(range)

    fireEvent.focus(container.querySelector('.ProseMirror')!)
    document.dispatchEvent(new Event('selectionchange'))

    expect(promptContextInserter).not.toBeNull()

    await act(async () => {
      promptContextInserter!('/badgerdoc/document/123/page/2')
    })

    await waitFor(() => {
      expect(latestValue).toBe('Hello {{/badgerdoc/document/123/page/2}}world')
    })
  })
})
