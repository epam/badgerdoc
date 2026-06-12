import { Plugin, PluginKey } from '@tiptap/pm/state'

export const extractionChatScopePluginKey = new PluginKey('extractionBlockChatScope')

interface ChatScopePluginState {
  blockIdsInChatScope: string[]
  pageNumbersInChatScope: number[]
  isWholeDocumentInChatScope: boolean
  isInteractionDisabled: boolean
}

export interface ChatScopePluginMeta {
  blockIds: string[]
  pageNumbers: number[]
  isWholeDocumentSelected: boolean
  isInteractionDisabled?: boolean
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
          isInteractionDisabled: false,
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
          isInteractionDisabled: meta.isInteractionDisabled ?? false,
        }
      },
    },
  })
}
