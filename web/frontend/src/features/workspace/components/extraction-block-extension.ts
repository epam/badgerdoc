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
      clearBlockChatScope: () => ReturnType
      setBlockChatScope: (blockId: string) => ReturnType
    }
  }
}

interface ExtractionBlockOptions {
  onBlockSelect?: (blockId: string | null, pageNumber: number | null) => void
  onBlockDelete?: (blockId: string, pageNumber: number | null) => void
  onWillDeleteNode?: () => void
  addBlockToScope: (blockId: string) => void
  removeBlockFromScope: (blockId: string) => void
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
      onWillDeleteNode: undefined,
      addBlockToScope: () => undefined,
      removeBlockFromScope: () => undefined,
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
      clearBlockChatScope:
        () =>
        ({ tr, dispatch, state }) => {
          if (dispatch) {
            // Get current block in scope to notify removal
            const pluginState = extractionChatScopePluginKey.getState(state)
            const currentBlockId = pluginState?.blockIdInChatScope

            const meta: ChatScopePluginMeta = { blockId: null }
            dispatch(tr.setMeta(extractionChatScopePluginKey, meta))

            // Notify removal callback if there was a block in scope
            if (currentBlockId) {
              this.options.removeBlockFromScope(currentBlockId)
            }
          }
          return true
        },
      setBlockChatScope:
        (blockId: string) =>
        ({ tr, dispatch }) => {
          if (dispatch) {
            const meta: ChatScopePluginMeta = { blockId }
            dispatch(tr.setMeta(extractionChatScopePluginKey, meta))
            this.options.addBlockToScope(blockId)
          }
          return true
        },
    }
  },

  addKeyboardShortcuts() {
    const isSelectionInExtractionBlock = () => {
      const { $from } = this.editor.state.selection
      for (let depth = $from.depth; depth > 0; depth--) {
        if ($from.node(depth).type.name === this.name) {
          return true
        }
      }
      return false
    }

    const splitToParagraphInBlock = () => {
      if (!isSelectionInExtractionBlock()) {
        return false
      }

      // Keep Enter behavior scoped to paragraph splitting inside the block.
      return this.editor.commands.splitBlock()
    }

    return {
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
