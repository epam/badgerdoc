import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

export const extractionChatScopePluginKey = new PluginKey('extractionBlockChatScope')

interface ChatScopePluginState {
  blockIdsInChatScope: string[]
  pageNumbersInChatScope: number[]
  isWholeDocumentInChatScope: boolean
}

export interface ChatScopePluginMeta {
  blockIds: string[]
  pageNumbers: number[]
  isWholeDocumentSelected: boolean
}

export function createExtractionChatScopePlugin() {
  return new Plugin<ChatScopePluginState>({
    key: extractionChatScopePluginKey,

    state: {
      init(): ChatScopePluginState {
        return {
          blockIdsInChatScope: [],
          pageNumbersInChatScope: [],
          isWholeDocumentInChatScope: false,
        }
      },

      apply(tr, value): ChatScopePluginState {
        const meta = tr.getMeta(extractionChatScopePluginKey) as ChatScopePluginMeta | undefined
        if (!meta) {
          return value
        }
        return {
          blockIdsInChatScope: meta.blockIds ?? [],
          pageNumbersInChatScope: meta.pageNumbers ?? [],
          isWholeDocumentInChatScope: meta.isWholeDocumentSelected ?? false,
        }
      },
    },

    props: {
      decorations(state) {
        const pluginState = extractionChatScopePluginKey.getState(state)
        const selectedBlockIds = new Set(pluginState?.blockIdsInChatScope ?? [])
        const selectedPageNumbers = new Set(pluginState?.pageNumbersInChatScope ?? [])
        const isWholeDocumentSelected = pluginState?.isWholeDocumentInChatScope ?? false
        if (
          !isWholeDocumentSelected &&
          selectedBlockIds.size === 0 &&
          selectedPageNumbers.size === 0
        ) {
          return DecorationSet.empty
        }

        const decorations: Decoration[] = []

        state.doc.descendants((node, pos) => {
          if (node.type.name === 'extractionBlock') {
            const blockId = node.attrs.blockId as string
            const pageNumber = Number(node.attrs.page)
            const isPageSelected =
              Number.isFinite(pageNumber) && selectedPageNumbers.has(pageNumber)

            if (
              isWholeDocumentSelected ||
              isPageSelected ||
              (blockId && selectedBlockIds.has(blockId))
            ) {
              decorations.push(
                Decoration.node(pos, pos + node.nodeSize, {
                  class: 'bg-primary/5',
                })
              )
            }
          }
        })

        return DecorationSet.create(state.doc, decorations)
      },
    },
  })
}
