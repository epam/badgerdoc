import { Dispatch, SetStateAction, useCallback, useState } from 'react'
import { FileText } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton.tsx'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import ExtractionEditor from '@/features/workspace/components/extraction-editor'
import { ExtractionChat } from '@/features/workspace/components/extraction-chat'
import { useFormattedExtractionContent } from '@/features/workspace/hooks/use-formatted-extraction-content'
import type { ExtractionChatContextProps } from '@/features/workspace/helpers/extraction-chat-context'

interface ExtractionResultsTabProps {
  isLoading: boolean
  extractionPages?: BadgerDocExtractionPage[]
  tag: string
  hasUnsavedChanges: boolean
  onBaselineReady: (html: string) => void
  onContentChange: (html: string) => void
  onRevertChanges: () => void
  onAcceptChanges: () => Promise<void>
  onSaveExtraction: () => Promise<void>
  onBlockDelete: (blockId: string, pageNumber: number | null) => void
  isSaving?: boolean
  activeBlockId: string | null
  onBlockSelect: (blockId: string | null) => void
  onPageNavigate: Dispatch<SetStateAction<number>>
  currentPage: number
  documentId: string
  chatContext: ExtractionChatContextProps
}

function ExtractionEmptyState({ tag }: { tag: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <FileText className="mb-4 h-12 w-12 text-muted-foreground" />
      <h3 className="text-lg font-medium">No data available</h3>
      <p className="mt-1 text-sm text-muted-foreground">No extraction data found for "{tag}"</p>
    </div>
  )
}

export function ExtractionResultsTab({
  tag,
  isLoading,
  extractionPages,
  hasUnsavedChanges,
  onBaselineReady,
  onContentChange,
  onRevertChanges,
  onAcceptChanges,
  onSaveExtraction,
  onBlockDelete,
  isSaving,
  onBlockSelect,
  activeBlockId,
  onPageNavigate,
  currentPage,
  documentId,
  chatContext,
}: ExtractionResultsTabProps) {
  const [isRunningInference, setIsRunningInference] = useState(false)
  const isEmpty = !extractionPages || extractionPages.length === 0

  const extractionHtmlContent = useFormattedExtractionContent(extractionPages)

  const handleBlockSelect = useCallback(
    (blockId: string | null, pageNumber: number | null) => {
      onBlockSelect(blockId)
      if (pageNumber !== null) {
        onPageNavigate(() => pageNumber)
      }
    },
    [onBlockSelect, onPageNavigate]
  )

  return (
    <div className="flex h-full flex-col bg-card overflow-hidden">
      <div className="flex-1 min-h-0">
        {isLoading && (
          <div className="flex items-center flex-col justify-center h-full w-full p-2 space-y-2">
            <Skeleton className="h-20 grow w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        )}
        {!isLoading && isEmpty && <ExtractionEmptyState tag={tag} />}
        {!isLoading && !isEmpty && (
          <ExtractionEditor
            content={extractionHtmlContent}
            hasUnsavedChanges={hasUnsavedChanges}
            isSaving={isSaving}
            onBaselineReady={onBaselineReady}
            onContentChange={onContentChange}
            onSaveExtraction={onSaveExtraction}
            onRevertChanges={onRevertChanges}
            onAcceptChanges={onAcceptChanges}
            onBlockDelete={onBlockDelete}
            selectedContextBlockIds={chatContext.selectedBlocks.map((block) => block.blockId)}
            selectedContextPages={chatContext.selectedPages}
            isWholeDocumentSelected={chatContext.isWholeDocumentSelected}
            onToggleBlockContext={chatContext.onToggleBlock}
            activeBlockId={activeBlockId}
            onBlockSelect={handleBlockSelect}
          />
        )}
      </div>
      <ExtractionChat
        documentId={documentId}
        currentPage={currentPage}
        canAddWholeDocument
        canAddCurrentPage
        prompt={chatContext.prompt}
        isWholeDocumentSelected={chatContext.isWholeDocumentSelected}
        selectedPages={chatContext.selectedPages}
        onPromptChange={chatContext.onPromptChange}
        onAddWholeDocument={chatContext.onAddWholeDocument}
        onAddCurrentPage={chatContext.onAddCurrentPage}
        disabled={isLoading || hasUnsavedChanges || isSaving}
        isProcessing={isRunningInference}
        setIsRunningInference={setIsRunningInference}
        activeTag={tag}
      />
    </div>
  )
}
