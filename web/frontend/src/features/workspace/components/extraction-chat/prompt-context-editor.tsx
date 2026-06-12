import { useEffect, useMemo, useRef, type MouseEvent } from 'react'
import { Node as TiptapNode, mergeAttributes } from '@tiptap/core'
import { Plugin, Selection, TextSelection } from '@tiptap/pm/state'
import type { NodeViewProps } from '@tiptap/react'
import { EditorContent, NodeViewWrapper, ReactNodeViewRenderer, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { X } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/helpers/utils'
import {
  findPromptContextLinks,
  formatPromptContextLink,
  getPromptContextTokenLabel,
  type PromptContextPathInserterRegistration,
} from '@/features/workspace/helpers/extraction-chat-context'
import { createPromptEditorContent, serializePromptEditorDoc } from './prompt-context-editor-utils'

interface PromptContextEditorProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
  canSubmit?: boolean
  onSubmitShortcut?: () => void
  onRegisterContextInserter?: PromptContextPathInserterRegistration
}

function isApplePlatform() {
  if (typeof navigator === 'undefined') {
    return false
  }

  const platform =
    (navigator as Navigator & { userAgentData?: { platform?: string } }).userAgentData?.platform ??
    navigator.platform ??
    ''

  return /Mac|iPhone|iPad|iPod/i.test(platform)
}

function isSubmitShortcut(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.altKey || event.shiftKey || event.isComposing) {
    return false
  }

  return isApplePlatform() ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey
}

function getDomCursorPosition(editor: NonNullable<ReturnType<typeof useEditor>>) {
  const selection = editor.view.dom.ownerDocument.getSelection()
  const anchorNode = selection?.anchorNode

  if (!selection?.isCollapsed || !anchorNode) {
    return null
  }

  const anchorElement =
    anchorNode.nodeType === Node.TEXT_NODE ? anchorNode.parentElement : anchorNode
  if (!anchorElement || !editor.view.dom.contains(anchorElement)) {
    return null
  }

  try {
    return editor.view.posAtDOM(anchorNode, selection.anchorOffset)
  } catch {
    return null
  }
}

function PromptContextTokenView({ node, deleteNode }: NodeViewProps) {
  const path = String(node.attrs.path ?? '')

  const handleRemove = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault()
    event.stopPropagation()
    deleteNode()
  }

  return (
    <NodeViewWrapper
      as="span"
      data-prompt-context-token
      data-context-path={path}
      contentEditable={false}
      className="inline-flex align-baseline"
    >
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="mx-0.5 inline-flex h-6 max-w-full select-none items-center gap-1 rounded border border-blue-200 bg-blue-50 px-1.5 text-xs font-medium text-blue-700">
            <span className="truncate">{getPromptContextTokenLabel(path)}</span>
            <button
              type="button"
              className="rounded-sm p-0.5 text-blue-500 hover:bg-blue-100 hover:text-blue-700"
              onClick={handleRemove}
              aria-label={`Remove ${path}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        </TooltipTrigger>
        <TooltipContent side="top">{path}</TooltipContent>
      </Tooltip>
    </NodeViewWrapper>
  )
}

export const PromptContextToken = TiptapNode.create({
  name: 'promptContextToken',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      path: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-context-path'),
        renderHTML: (attributes) => ({
          'data-context-path': attributes.path,
        }),
      },
    }
  },

  parseHTML() {
    return [{ tag: 'span[data-prompt-context-token]' }]
  },

  renderHTML({ HTMLAttributes }) {
    const path = String(HTMLAttributes['data-context-path'] ?? HTMLAttributes.path ?? '')

    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-prompt-context-token': '',
        'data-context-path': path,
        title: path,
      }),
      getPromptContextTokenLabel(path),
    ]
  },

  renderText({ node }) {
    return formatPromptContextLink(String(node.attrs.path ?? ''))
  },

  addNodeView() {
    return ReactNodeViewRenderer(PromptContextTokenView)
  },

  addProseMirrorPlugins() {
    const tokenType = this.type

    return [
      new Plugin({
        appendTransaction: (transactions, _oldState, newState) => {
          if (!transactions.some((transaction) => transaction.docChanged)) {
            return null
          }

          const replacements: { from: number; to: number; path: string }[] = []

          newState.doc.descendants((node, pos) => {
            if (!node.isText || !node.text) {
              return
            }

            findPromptContextLinks(node.text).forEach(({ raw, path, index }) => {
              replacements.push({
                from: pos + index,
                to: pos + index + raw.length,
                path,
              })
            })
          })

          if (!replacements.length) {
            return null
          }

          const tr = newState.tr

          replacements
            .sort((left, right) => right.from - left.from)
            .forEach(({ from, to, path }) => {
              tr.replaceWith(from, to, tokenType.create({ path }))
            })

          return tr.docChanged ? tr : null
        },
      }),
    ]
  },
})

export function PromptContextEditor({
  value,
  onChange,
  disabled,
  placeholder,
  className,
  canSubmit = false,
  onSubmitShortcut,
  onRegisterContextInserter,
}: PromptContextEditorProps) {
  const canSubmitRef = useRef(canSubmit)
  const onSubmitShortcutRef = useRef(onSubmitShortcut)
  const lastSelectionRef = useRef<number | null>(null)

  useEffect(() => {
    canSubmitRef.current = canSubmit
    onSubmitShortcutRef.current = onSubmitShortcut
  }, [canSubmit, onSubmitShortcut])

  const extensions = useMemo(
    () => [
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
    []
  )
  const editor = useEditor({
    extensions,
    content: createPromptEditorContent(value),
    editable: !disabled,
    editorProps: {
      attributes: {
        class:
          'min-h-28 max-h-56 w-full overflow-y-auto px-4 pt-2 pb-2 whitespace-pre-wrap focus:outline-none',
      },
      handleKeyDown: (_view, event) => {
        if (!isSubmitShortcut(event)) {
          return false
        }

        if (!canSubmitRef.current || !onSubmitShortcutRef.current) {
          return false
        }

        event.preventDefault()
        onSubmitShortcutRef.current()
        return true
      },
    },
    onUpdate: ({ editor, transaction }) => {
      if (!transaction.docChanged) return

      onChange(serializePromptEditorDoc(editor.state.doc))
    },
    onSelectionUpdate: ({ editor }) => {
      const { empty, from } = editor.state.selection
      lastSelectionRef.current = empty ? from : null
    },
    onFocus: ({ editor }) => {
      const { empty, from } = editor.state.selection
      lastSelectionRef.current = empty ? from : null
    },
  })

  useEffect(() => {
    if (!editor) return

    editor.setEditable(!disabled)
  }, [disabled, editor])

  useEffect(() => {
    if (!editor) return

    const serialized = serializePromptEditorDoc(editor.state.doc)

    if (serialized !== value) {
      editor.commands.setContent(createPromptEditorContent(value), { emitUpdate: false })
    }
  }, [editor, value])

  useEffect(() => {
    if (!editor) return

    onRegisterContextInserter?.((path) => {
      if (!editor.isEditable) {
        return
      }

      const endSelection = Selection.atEnd(editor.state.doc)
      const shouldAppendAtEnd = !editor.isFocused
      const currentSelection = (() => {
        if (shouldAppendAtEnd) {
          return endSelection
        }

        const liveCursorPosition = getDomCursorPosition(editor)
        const savedCursorPosition =
          lastSelectionRef.current === null
            ? null
            : Math.min(Math.max(lastSelectionRef.current, 1), endSelection.from)

        if (liveCursorPosition !== null) {
          return TextSelection.create(editor.state.doc, liveCursorPosition)
        }

        return savedCursorPosition === null
          ? endSelection
          : TextSelection.create(editor.state.doc, savedCursorPosition)
      })()

      const tokenNode = editor.state.schema.nodes.promptContextToken.create({ path })
      const docText = editor.state.doc.textContent
      const needsSpace = shouldAppendAtEnd && docText.length > 0 && !/\s$/.test(docText)

      const transaction = editor.state.tr.setSelection(currentSelection)
      if (needsSpace) transaction.insertText(' ')
      transaction.replaceSelectionWith(tokenNode, false)

      editor.view.dispatch(transaction)
      lastSelectionRef.current = editor.state.selection.from
    })

    return () => onRegisterContextInserter?.(null)
  }, [editor, onRegisterContextInserter])

  return (
    <div
      className={cn(
        'relative w-full cursor-text text-sm disabled:cursor-not-allowed',
        disabled && 'pointer-events-none opacity-60',
        className
      )}
    >
      {!value && placeholder && (
        <div className="pointer-events-none absolute top-2 left-4 text-muted-foreground">
          {placeholder}
        </div>
      )}
      <EditorContent
        editor={editor}
        className={cn(
          'max-h-56 min-h-28 w-full max-w-full overflow-y-auto',
          '[&_.ProseMirror]:outline-none [&_.ProseMirror_p]:my-0'
        )}
      />
    </div>
  )
}
