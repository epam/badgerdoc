import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

export const extractionChatScopePluginKey = new PluginKey('extractionBlockChatScope')

interface ChatScopePluginState {
  blockIdInChatScope: string | null
}

export interface ChatScopePluginMeta {
  blockId: string | null
}

export function createExtractionChatScopePlugin() {
  return new Plugin<ChatScopePluginState>({
    key: extractionChatScopePluginKey,

    state: {
      init(): ChatScopePluginState {
        return {
          blockIdInChatScope: null,
        }
      },

      apply(tr, value): ChatScopePluginState {
        const meta = tr.getMeta(extractionChatScopePluginKey) as ChatScopePluginMeta | undefined
        if (!meta) {
          return value
        }
        return {
          blockIdInChatScope: meta.blockId ?? null,
        }
      },
    },

    props: {
      decorations(state) {
        const pluginState = extractionChatScopePluginKey.getState(state)
        if (!pluginState || !pluginState.blockIdInChatScope) {
          return DecorationSet.empty
        }

        const decorations: Decoration[] = []

        state.doc.descendants((node, pos) => {
          if (node.type.name === 'extractionBlock') {
            const blockId = node.attrs.blockId as string
            if (blockId && blockId === pluginState.blockIdInChatScope) {
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
