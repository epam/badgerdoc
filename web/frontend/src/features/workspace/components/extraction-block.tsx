import { NodeViewContent, NodeViewWrapper, NodeViewProps } from '@tiptap/react'
import { MessageCirclePlus, MessageCircleOff, Trash2 } from 'lucide-react'
import type { MouseEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { extractionChatScopePluginKey } from './extraction-context-plugin'
import { cn } from '@/helpers/utils'

interface ExtractionBlockProps extends NodeViewProps {
  onBlockSelect?: (blockId: string | null, pageNumber: number | null) => void
  onBlockDelete?: (blockId: string, pageNumber: number | null) => void
}

export function ExtractionBlock({ node, editor, extension, deleteNode }: ExtractionBlockProps) {
  const { blockId, title, type, page, isNew } = node.attrs
  const onBlockSelect = extension.options.onBlockSelect
  const onBlockDelete = extension.options.onBlockDelete
  const onToggleBlockContext = extension.options.onToggleBlockContext

  const chatScopePluginState = extractionChatScopePluginKey.getState(editor.state)
  const parsedPage = Number(page)
  const pageNumber = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : null
  const isExplicitlyInChatScope = (chatScopePluginState?.blockIdsInChatScope ?? []).includes(blockId)
  const isPageInChatScope =
    pageNumber !== null && (chatScopePluginState?.pageNumbersInChatScope ?? []).includes(pageNumber)
  const isWholeDocumentInChatScope = chatScopePluginState?.isWholeDocumentInChatScope ?? false
  const isBlockedByHigherLevelContext = isPageInChatScope || isWholeDocumentInChatScope
  const isInChatScope = isExplicitlyInChatScope || isBlockedByHigherLevelContext
  const blockContextTitle = isWholeDocumentInChatScope
    ? 'Whole document already in context'
    : isPageInChatScope
      ? `Page ${pageNumber} already in context`
      : isExplicitlyInChatScope
        ? 'Remove block from context'
        : 'Add block to context'

  const handleToggleBlockScope = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault()
    event.stopPropagation()

    onToggleBlockContext?.(blockId, pageNumber)
  }

  const handleWrapperMouseDown = (event: MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement
    const isInsideContent = Boolean(target.closest('[data-node-view-content]'))
    const isInsideInteractivePanel = Boolean(target.closest('[data-extraction-interactive="true"]'))
    const isButton = target.closest('button') !== null

    // Allow normal focus/editing inside content; only block interactive chrome.
    if (isButton || isInsideInteractivePanel) {
      event.preventDefault()
      event.stopPropagation()
      return
    }

    if (!isInsideContent) {
      event.preventDefault()
      event.stopPropagation()
    }
  }

  const handleHeaderClick = () => {
    if (!onBlockSelect || !blockId) return
    onBlockSelect(blockId, pageNumber)
  }

  const handleDeleteBlock = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault()
    event.stopPropagation()

    if (!blockId) {
      return
    }

    extension.options.onWillDeleteNode?.()
    deleteNode()
    onBlockDelete?.(blockId, pageNumber)
  }

  return (
    <NodeViewWrapper
      data-block-id={blockId}
      data-block-title={title}
      className={cn('border-b transition-colors duration-150 ease-out focus-within:bg-primary/5', {
        'border-l-2 border-l-amber-400 bg-amber-50/40': isNew,
      })}
      onMouseDown={handleWrapperMouseDown}
    >
      {(type || page || isNew) && (
        <div
          className="flex gap-2 p-4 pb-2 items-center [&>span:not(:last-of-type)]:after:content-['·'] [&>span:not(:last-child)]:after:ml-2 cursor-pointer"
          contentEditable={false}
          onClick={handleHeaderClick}
        >
          {isNew && (
            <Badge
              variant="outline"
              className="border-amber-400 bg-amber-100 text-amber-700 text-[10px] px-1.5 py-0"
            >
              New
            </Badge>
          )}
          {type && <span className="text-xs text-muted-foreground capitalize">{type}</span>}
          {page && <span className="text-xs text-muted-foreground">Page {page}</span>}
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handleToggleBlockScope}
            className="cursor-pointer size-7"
            title={blockContextTitle}
            aria-label={blockContextTitle}
            disabled={isBlockedByHigherLevelContext}
          >
            {isInChatScope ? <MessageCircleOff /> : <MessageCirclePlus />}
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            onClick={handleDeleteBlock}
            className="hover:text-destructive ml-auto cursor-pointer size-7"
            title="Delete block"
          >
            <Trash2 />
          </Button>
        </div>
      )}

      <NodeViewContent
        className={cn('px-4 pb-4 min-h-[2.5rem]', {
          'min-h-[3rem] rounded-md border border-dashed border-amber-300 bg-white mx-4 mb-4 p-2 focus-within:border-amber-500 focus-within:ring-1 focus-within:ring-amber-500/30':
            isNew,
        })}
      />
    </NodeViewWrapper>
  )
}
