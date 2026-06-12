import { useMemo } from 'react'
import type { PageChatContext } from '@/components/collection-viewer/viewer-toolbar'
import {
  getCurrentPageTooltip,
  getDocumentContextTooltip,
} from '@/features/workspace/helpers/extraction-chat-context'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'

interface UseViewerChatContextParams {
  canAddContext: boolean
  currentPage: number
  selectedPages: number[]
  isWholeDocumentSelected: boolean
  isContextInteractionDisabled: boolean
  workflowSelection: Pick<
    ChatWorkflowSelection,
    'isWorkflowsLoading' | 'canUseDocumentContext' | 'canUsePageContext'
  >
  onAddWholeDocument: () => void
  onAddCurrentPage: () => void
}

export function useViewerChatContext({
  canAddContext,
  currentPage,
  selectedPages,
  isWholeDocumentSelected,
  isContextInteractionDisabled,
  workflowSelection,
  onAddWholeDocument,
  onAddCurrentPage,
}: UseViewerChatContextParams) {
  return useMemo<PageChatContext>(() => {
    const isBaseDisabled = isContextInteractionDisabled || workflowSelection.isWorkflowsLoading
    const isCurrentPageSelected = selectedPages.includes(currentPage)

    return {
      canAddWholeDocumentToContext: canAddContext,
      isWholeDocumentInContext: isWholeDocumentSelected,
      isWholeDocumentContextDisabled: isBaseDisabled || !workflowSelection.canUseDocumentContext,
      wholeDocumentContextTooltip: getDocumentContextTooltip(
        workflowSelection.canUseDocumentContext,
        isWholeDocumentSelected
      ),
      onAddWholeDocumentToContext: onAddWholeDocument,
      canAddCurrentPageToContext: canAddContext,
      isCurrentPageInContext: isCurrentPageSelected,
      isCurrentPageContextDisabled: isBaseDisabled || !workflowSelection.canUsePageContext,
      currentPageContextTooltip: getCurrentPageTooltip({
        canUsePageContext: workflowSelection.canUsePageContext,
        isCurrentPageSelected,
        currentPage,
      }),
      onAddCurrentPageToContext: onAddCurrentPage,
    }
  }, [
    canAddContext,
    currentPage,
    selectedPages,
    isWholeDocumentSelected,
    isContextInteractionDisabled,
    workflowSelection.isWorkflowsLoading,
    workflowSelection.canUseDocumentContext,
    workflowSelection.canUsePageContext,
    onAddWholeDocument,
    onAddCurrentPage,
  ])
}
