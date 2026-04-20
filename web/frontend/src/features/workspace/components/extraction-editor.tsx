import { useCallback, useMemo, useRef, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import { ExtractionBlockExtension } from '@/features/workspace/components/extraction-block-extension.ts'
import { createExtractionTableExtensions } from '@/features/workspace/components/extraction-editor-extensions'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { toast } from 'sonner'

interface ExtractionEditorProps {
  content: string
  hasUnsavedChanges: boolean
  isSaving?: boolean
  onBaselineReady: (html: string) => void
  onContentChange: (html: string) => void
  onSaveExtraction?: () => Promise<void>
  onRevertChanges: () => void
  onAcceptChanges: () => Promise<void>
  onBlockDelete: (blockId: string, pageNumber: number | null) => void
  selectedContextBlockIds: string[]
  selectedContextPages: number[]
  isWholeDocumentSelected: boolean
  onToggleBlockContext: (blockId: string, pageNumber: number | null) => void
  activeBlockId: string | null
  onBlockSelect: (blockId: string | null, pageNumber: number | null) => void
}

const ExtractionEditor = ({
  content,
  hasUnsavedChanges,
  isSaving,
  onBaselineReady,
  onContentChange,
  onSaveExtraction,
  onRevertChanges,
  onAcceptChanges,
  onBlockDelete,
  selectedContextBlockIds,
  selectedContextPages,
  isWholeDocumentSelected,
  onToggleBlockContext,
  activeBlockId,
  onBlockSelect,
}: ExtractionEditorProps) => {
  const isAcceptingRef = useRef(false)
  const isRevertingRef = useRef(false)
  const skipNextContentSyncRef = useRef(false)
  const selectionTriggeredInEditorBlockIdRef = useRef<string | null>(null)
  const cursorBlockIdRef = useRef<string | null>(null)
  const editorHasFocusedRef = useRef(false)
  const lastCleanContentRef = useRef(content || '')
  const hasChanges = hasUnsavedChanges

  const handleBlockSelectFromEditor = useCallback(
    (blockId: string | null, pageNumber: number | null) => {
      selectionTriggeredInEditorBlockIdRef.current = blockId
      onBlockSelect(blockId, pageNumber)
    },
    [onBlockSelect]
  )

  const handleWillDeleteNode = useCallback(() => {
    skipNextContentSyncRef.current = true
  }, [])

  const extensions = useMemo(
    () => [
      ...createExtractionTableExtensions(),
      ExtractionBlockExtension.configure({
        onBlockSelect: handleBlockSelectFromEditor,
        onBlockDelete,
        onToggleBlockContext,
        onWillDeleteNode: handleWillDeleteNode,
      }),
    ],
    [handleBlockSelectFromEditor, onBlockDelete, onToggleBlockContext, handleWillDeleteNode]
  )

  const editor = useEditor({
    extensions,
    content: content,
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none',
      },
      editable: function isEditable(state) {
        const { $from } = state.selection
        for (let depth = $from.depth; depth > 0; depth--) {
          const node = $from.node(depth)
          if (node.type.name === 'customTab') {
            const modelAttr = node.attrs?.model
            return modelAttr === 'council'
          }
        }
        return true
      },
    },
    onCreate: ({ editor }) => {
      onBaselineReady(editor.getHTML())
    },
    onUpdate: ({ editor, transaction }) => {
      if (!transaction.docChanged) return
      if (transaction.getMeta('ignoreUnsavedChanges')) return

      onContentChange(editor.getHTML())
    },
    onDestroy: async () => {
      await handleAcceptChanges()
    },
    onFocus: () => {
      editorHasFocusedRef.current = true
    },
    onSelectionUpdate: ({ editor }) => {
      if (!editorHasFocusedRef.current) return
      const { $from } = editor.state.selection
      let blockId: string | null = null
      let page: string | null = null
      for (let depth = $from.depth; depth > 0; depth--) {
        const node = $from.node(depth)
        if (node.type.name === 'extractionBlock') {
          blockId = (node.attrs.blockId as string) ?? null
          page = (node.attrs.page as string) ?? null
          break
        }
      }

      if (blockId !== cursorBlockIdRef.current) {
        cursorBlockIdRef.current = blockId
        if (blockId) {
          const parsed = Number(page)
          const pageNumber = Number.isFinite(parsed) && parsed > 0 ? parsed : null
          handleBlockSelectFromEditor(blockId, pageNumber)
        }
      }
    },
    onBlur: async () => {
      if (isAcceptingRef.current || isRevertingRef.current) {
        return
      }
      if (onSaveExtraction) {
        await onSaveExtraction()
      }
    },
  })

  useEffect(
    function trackLastCleanContent() {
      if (!hasUnsavedChanges) {
        lastCleanContentRef.current = content || ''
      }
    },
    [content, hasUnsavedChanges]
  )

  useEffect(
    function syncExternalContent() {
      if (!editor) return

      const normalizedIncomingContent = content || ''
      if (editor.getHTML() === normalizedIncomingContent) {
        return
      }

      // After deleteNode() the editor already has the correct blocks removed.
      // Skip the full setContent() replacement to avoid destroying all NodeViews.
      if (skipNextContentSyncRef.current) {
        skipNextContentSyncRef.current = false
        onBaselineReady(editor.getHTML())
        return
      }

      // When new blocks are added (e.g. from the PDF viewer) but existing blocks
      // haven't been removed, insert only the new blocks to preserve text edits.
      const parser = new DOMParser()
      const incomingDoc = parser.parseFromString(normalizedIncomingContent, 'text/html')
      const incomingBlockIds = new Set<string>()
      incomingDoc
        .querySelectorAll('.ocr_carea[id]')
        .forEach((el) => incomingBlockIds.add(el.getAttribute('id')!))

      const editorBlockIds = new Set<string>()
      editor.state.doc.descendants((node) => {
        if (node.type.name === 'extractionBlock' && node.attrs.blockId) {
          editorBlockIds.add(node.attrs.blockId as string)
        }
      })

      const allEditorBlocksPreserved = [...editorBlockIds].every((id) => incomingBlockIds.has(id))
      const newBlockIds = [...incomingBlockIds].filter((id) => !editorBlockIds.has(id))

      // Suppress cursor-driven block selection during content mutations so the
      // editor doesn't auto-scroll to the wrong block.
      editorHasFocusedRef.current = false
      cursorBlockIdRef.current = null
      selectionTriggeredInEditorBlockIdRef.current = null

      if (allEditorBlocksPreserved && newBlockIds.length > 0) {
        for (const blockId of newBlockIds) {
          const blockEl = incomingDoc.getElementById(blockId)
          if (!blockEl) continue
          editor
            .chain()
            .setMeta('ignoreUnsavedChanges', true)
            .insertContentAt(editor.state.doc.content.size, blockEl.outerHTML)
            .run()
        }
        onBaselineReady(editor.getHTML())
        return
      }

      editor.commands.setContent(normalizedIncomingContent, { emitUpdate: false })
      onBaselineReady(editor.getHTML())
    },
    [editor, content, onBaselineReady]
  )

  useEffect(
    function syncChatContextBlocks() {
      if (!editor) return

      editor.commands.setBlockChatScope({
        blockIds: selectedContextBlockIds,
        pageNumbers: selectedContextPages,
        isWholeDocumentSelected,
      })
    },
    [editor, selectedContextBlockIds, selectedContextPages, isWholeDocumentSelected]
  )

  useEffect(
    function handleSelectedBlockChange() {
      if (!editor) return

      editor.commands.setSelectedExtractionBlock(activeBlockId ?? null)

      if (selectionTriggeredInEditorBlockIdRef.current === activeBlockId) {
        selectionTriggeredInEditorBlockIdRef.current = null
        return
      }

      selectionTriggeredInEditorBlockIdRef.current = null

      // Defer scroll so React node views have time to mount after a content sync
      const frame = requestAnimationFrame(() => {
        editor?.commands.scrollToExtractionBlock(activeBlockId ?? null)
      })
      return () => cancelAnimationFrame(frame)
    },
    [editor, activeBlockId]
  )

  const handleRevertChanges = useCallback(() => {
    editorHasFocusedRef.current = false
    cursorBlockIdRef.current = null
    selectionTriggeredInEditorBlockIdRef.current = null

    const cleanContent = lastCleanContentRef.current
    if (editor && editor.getHTML() !== cleanContent) {
      editor.commands.setContent(cleanContent, { emitUpdate: false })
      onBaselineReady(editor.getHTML())
    }
    onRevertChanges()
    isRevertingRef.current = false
  }, [editor, onBaselineReady, onRevertChanges])

  const handleAcceptChanges = useCallback(async () => {
    isAcceptingRef.current = true
    selectionTriggeredInEditorBlockIdRef.current = null

    try {
      await onAcceptChanges()
      if (editor) {
        onBaselineReady(editor.getHTML())
      }
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Something went wrong while accepting changes'
      toast.error(message)
    } finally {
      isAcceptingRef.current = false
      if (editor) {
        editor.setEditable(true)
      }
    }
  }, [editor, onAcceptChanges, onBaselineReady])

  return (
    <div className="relative flex h-full w-full flex-col bg-muted/30">
      {isSaving && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/10 backdrop-blur-sm">
          <div className="flex items-center gap-2 rounded-md bg-white/90 px-4 py-2 text-sm font-medium text-slate-700">
            <Spinner size="sm" />
            Saving changes...
          </div>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-hidden bg-card">
        <div className="h-full overflow-auto">
          <EditorContent editor={editor} />
        </div>
      </div>
      {hasChanges && (
        <div className="flex shrink-0 justify-center gap-3 border-t bg-card px-4 py-3">
          <Button
            onMouseDown={() => {
              isRevertingRef.current = true
            }}
            disabled={isSaving && !isRevertingRef.current}
            size="sm"
            variant="outline"
            onClick={handleRevertChanges}
            title="Revert changes"
          >
            Revert
          </Button>
          <Button
            onMouseDown={() => {
              isAcceptingRef.current = true
            }}
            disabled={isSaving && !isAcceptingRef.current}
            size="sm"
            onClick={handleAcceptChanges}
            title="Accept changes"
          >
            Accept
          </Button>
        </div>
      )}
    </div>
  )
}

export default ExtractionEditor
