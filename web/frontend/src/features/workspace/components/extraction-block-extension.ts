import { mergeAttributes, Node } from '@tiptap/core'
import {
  createExtractionBlockHighlightPlugin,
  extractionBlockHighlightPluginKey,
  type HighlightPluginMeta,
} from './extraction-highlight-plugin'
import {
  createExtractionChatScopePlugin,
  extractionChatScopePluginKey,
  type ChatScopePluginMeta,
} from './extraction-context-plugin'
import { ReactNodeViewRenderer } from '@tiptap/react'
import { ExtractionBlock } from './extraction-block'

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    extractionBlock: {
      scrollToExtractionBlock: (blockId: string | null) => ReturnType
      setSelectedExtractionBlock: (blockId: string | null) => ReturnType
      setBlockChatScope: (scope: ChatScopePluginMeta) => ReturnType
    }
  }
}

interface ExtractionBlockOptions {
  onBlockSelect?: (blockId: string | null, pageNumber: number | null) => void
  onBlockDelete?: (blockId: string, pageNumber: number | null) => void
  onToggleBlockContext?: (blockId: string, pageNumber: number | null) => void
  onWillDeleteNode?: () => void
}

export const ExtractionBlockExtension = Node.create<ExtractionBlockOptions>({
  name: 'extractionBlock',

  group: 'block',

  content: 'block+',

  isolating: true,

  addOptions() {
    return {
      onBlockSelect: undefined,
      onBlockDelete: undefined,
      onToggleBlockContext: undefined,
      onWillDeleteNode: undefined,
    }
  },

  addAttributes() {
    return {
      blockId: {
        default: null,
        parseHTML: (element) => element.getAttribute('id'),
        renderHTML: (attributes) => {
          if (!attributes.blockId) {
            return {}
          }
          return {
            'data-block-id': attributes.blockId,
          }
        },
      },
      htmlClass: {
        default: null,
        parseHTML: (element) => element.getAttribute('class'),
        renderHTML: (attributes) => {
          if (!attributes.htmlClass) return {}
          return { class: attributes.htmlClass }
        },
      },
      title: {
        default: null,
        parseHTML: (element) => element.getAttribute('title'),
        renderHTML: (attributes) => {
          if (!attributes.title) {
            return {}
          }
          return {
            'data-block-title': attributes.title,
          }
        },
      },
      page: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-page'),
        renderHTML: (attributes) => {
          if (!attributes.page) {
            return {}
          }
          return {
            'data-page': attributes.page,
          }
        },
      },
      isNew: {
        default: false,
        parseHTML: (element) => element.getAttribute('data-new') === 'true',
        renderHTML: (attributes) => {
          if (!attributes.isNew) {
            return {}
          }
          return {
            'data-new': 'true',
          }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div.ocr_carea',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes), 0]
  },

  addProseMirrorPlugins() {
    return [createExtractionBlockHighlightPlugin(), createExtractionChatScopePlugin()]
  },

  addCommands() {
    return {
      setSelectedExtractionBlock:
        (blockId) =>
        ({ tr, dispatch }) => {
          if (dispatch) {
            const meta: HighlightPluginMeta = { selectedBlockId: blockId }
            dispatch(tr.setMeta(extractionBlockHighlightPluginKey, meta))
          }
          return true
        },
      scrollToExtractionBlock:
        (blockId) =>
        ({ editor }) => {
          const blockElement = editor.view.dom.querySelector(`[data-block-id="${blockId}"]`)
          if (!blockElement) {
            return false
          }

          blockElement.scrollIntoView({ block: 'start', behavior: 'smooth' })
          return true
        },
      setBlockChatScope:
        (scope: ChatScopePluginMeta) =>
        ({ tr, dispatch }) => {
          if (dispatch) {
            dispatch(tr.setMeta(extractionChatScopePluginKey, scope))
          }
          return true
        },
    }
  },

  addKeyboardShortcuts() {
    const getSelectionInExtractionBlock = () => {
      const { selection } = this.editor.state
      if (!selection.empty) {
        return null
      }

      const { $from } = selection
      let blockDepth: number | null = null

      for (let depth = $from.depth; depth > 0; depth--) {
        if ($from.node(depth).type.name === this.name) {
          blockDepth = depth
          break
        }
      }

      if (blockDepth === null) {
        return null
      }

      return { $from, blockDepth }
    }

    const isSelectionInExtractionBlock = () => {
      return getSelectionInExtractionBlock() !== null
    }

    const isSelectionAtExtractionBlockStart = () => {
      const selectionInBlock = getSelectionInExtractionBlock()
      if (!selectionInBlock) {
        return false
      }

      const { $from, blockDepth } = selectionInBlock
      if ($from.parentOffset !== 0) {
        return false
      }

      for (let depth = $from.depth; depth > blockDepth; depth--) {
        if ($from.index(depth) !== 0) {
          return false
        }
      }

      return true
    }

    const splitToParagraphInBlock = () => {
      if (!isSelectionInExtractionBlock()) {
        return false
      }

      // Keep Enter behavior scoped to paragraph splitting inside the block.
      return this.editor.commands.splitBlock()
    }

    return {
      Backspace: () => {
        const selectionInBlock = getSelectionInExtractionBlock()
        if (!selectionInBlock || !isSelectionAtExtractionBlockStart()) {
          return false
        }

        return true
      },
      Enter: () => splitToParagraphInBlock(),
      'Shift-Enter': () => {
        return splitToParagraphInBlock()
      },
    }
  },

  addNodeView() {
    return ReactNodeViewRenderer(ExtractionBlock)
  },
})
