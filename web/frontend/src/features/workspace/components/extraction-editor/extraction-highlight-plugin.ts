import type { Node as ProseMirrorNode } from '@tiptap/pm/model'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

const SELECTED_EXTRACTION_BLOCK_CLASS = 'ring-2 ring-primary/35 ring-inset'

export const extractionBlockHighlightPluginKey = new PluginKey('extractionBlockHighlight')

interface HighlightPluginState {
  selectedBlockId: string | null
  decorations: DecorationSet
}

export interface HighlightPluginMeta {
  selectedBlockId: string | null
}

function createHighlightDecorations(
  doc: ProseMirrorNode,
  selectedBlockId: string | null
): DecorationSet {
  if (!selectedBlockId) {
    return DecorationSet.empty
  }

  const decorations: Decoration[] = []
  doc.descendants((node, pos) => {
    if (node.type.name !== 'extractionBlock') {
      return true
    }

    if (node.attrs.blockId === selectedBlockId) {
      decorations.push(
        Decoration.node(pos, pos + node.nodeSize, { class: SELECTED_EXTRACTION_BLOCK_CLASS })
      )
    }

    return true
  })

  return DecorationSet.create(doc, decorations)
}

function createHighlightPluginState(
  doc: ProseMirrorNode,
  selectedBlockId: string | null
): HighlightPluginState {
  return {
    selectedBlockId,
    decorations: createHighlightDecorations(doc, selectedBlockId),
  }
}

export function createExtractionBlockHighlightPlugin(): Plugin {
  return new Plugin({
    key: extractionBlockHighlightPluginKey,
    state: {
      init: (_config, state) => createHighlightPluginState(state.doc, null),
      apply: (tr, pluginState: HighlightPluginState, _oldState, newState) => {
        const meta = tr.getMeta(extractionBlockHighlightPluginKey) as
          | HighlightPluginMeta
          | undefined
        const hasMeta = meta !== undefined

        if (!tr.docChanged && !hasMeta) {
          return pluginState
        }

        const selectedBlockId = hasMeta ? meta.selectedBlockId : pluginState.selectedBlockId
        return createHighlightPluginState(newState.doc, selectedBlockId)
      },
    },
    props: {
      decorations: (state) => {
        const pluginState = extractionBlockHighlightPluginKey.getState(state) as
          | HighlightPluginState
          | undefined

        return pluginState?.decorations ?? DecorationSet.empty
      },
    },
  })
}
