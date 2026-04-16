import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { ChevronDown, File, Layers, SendHorizonal, X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Textarea } from '@/components/ui/textarea'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/helpers/utils'
import {
  getContextBlockLabel,
  type ExtractionContextBlock,
  type ExtractionContextPayload,
} from '@/features/workspace/helpers/extraction-chat-context'
import { extractionPagesKeys } from '@/shared/api/hooks/use-badgerdoc-extraction-pages'
import {
  useChatWorkflows,
  useTriggerWorkflow,
  useWorkflowStatus,
} from '@/shared/api/hooks/use-workflows'
import { Spinner } from '@/components/ui/spinner'
import { toast } from 'sonner'

function buildWorkflowTriggerPayload({
  documentId,
  contextPayload,
  currentPage,
  prompt,
  supportsPrompts,
}: {
  documentId: string
  contextPayload: ExtractionContextPayload
  currentPage: number
  prompt: string
  supportsPrompts: boolean
}) {
  const primaryPage =
    contextPayload.pages[0]?.page_number ?? contextPayload.blocks[0]?.pageNumber ?? currentPage

  return {
    document_id: Number(documentId),
    scope: contextPayload.kind === 'document' ? 'document' : 'page',
    page_number: contextPayload.kind === 'document' ? undefined : primaryPage,
    parameters: {
      context: contextPayload,
      ...(supportsPrompts && prompt
        ? {
            llm_params: {
              prompt,
            },
          }
        : {}),
    },
  } satisfies Record<string, unknown>
}

function getDocumentContextTooltip(
  canUseDocumentContext: boolean,
  isWholeDocumentSelected: boolean
) {
  if (!canUseDocumentContext) {
    return 'Whole document is not available for this workflow'
  }

  return isWholeDocumentSelected ? 'Whole document already added to context' : 'Add whole document'
}

function getCurrentPageTooltip({
  canUsePageContext,
  isWholeDocumentSelected,
  isCurrentPageSelected,
  currentPage,
}: {
  canUsePageContext: boolean
  isWholeDocumentSelected: boolean
  isCurrentPageSelected: boolean
  currentPage: number
}) {
  if (!canUsePageContext) {
    return 'Current page context is not available for this workflow'
  }

  if (isWholeDocumentSelected) {
    return 'Whole document already added to context'
  }

  return isCurrentPageSelected ? `Remove Page ${currentPage} from context` : 'Add current page'
}

function ContextChip({
  children,
  ariaLabel,
  icon,
  onRemove,
  title,
  variant = 'secondary',
}: {
  children: ReactNode
  ariaLabel: string
  icon?: ReactNode
  onRemove: () => void
  title?: string
  variant?: 'secondary' | 'outline'
}) {
  return (
    <Badge variant={variant} className="h-6 gap-1 pr-1 text-xs" title={title}>
      {icon}
      {children}
      <button
        type="button"
        className="ml-1 rounded-sm p-0.5 hover:bg-black/5"
        onClick={onRemove}
        aria-label={ariaLabel}
      >
        <X className="h-3 w-3" />
      </button>
    </Badge>
  )
}

function ContextSection({
  hasContext,
  isWholeDocumentSelected,
  selectedPages,
  selectedBlocks,
  onClearContext,
  onRemovePage,
  onRemoveBlock,
}: {
  hasContext: boolean
  isWholeDocumentSelected: boolean
  selectedPages: number[]
  selectedBlocks: ExtractionContextBlock[]
  onClearContext: () => void
  onRemovePage: (pageNumber: number) => void
  onRemoveBlock: (blockId: string) => void
}) {
  return (
    <div className="flex min-h-6 flex-wrap items-center gap-1.5">
      {!hasContext && (
        <span className="text-sm text-muted-foreground">
          Add document, page, or blocks to define the prompt context.
        </span>
      )}

      {isWholeDocumentSelected && (
        <ContextChip
          icon={<Layers className="h-3 w-3" />}
          ariaLabel="Remove whole document context"
          onRemove={onClearContext}
        >
          Whole document
        </ContextChip>
      )}

      {selectedPages.map((pageNumber) => (
        <ContextChip
          key={pageNumber}
          icon={<File className="h-3 w-3" />}
          ariaLabel={`Remove page ${pageNumber} from context`}
          onRemove={() => onRemovePage(pageNumber)}
        >
          {`Page ${pageNumber}`}
        </ContextChip>
      ))}

      {selectedBlocks.map((block) => (
        <ContextChip
          key={block.blockId}
          ariaLabel={`Remove ${block.blockId} from context`}
          onRemove={() => onRemoveBlock(block.blockId)}
          title={block.blockId}
          variant="outline"
        >
          {getContextBlockLabel(block.blockId)}
        </ContextChip>
      ))}
    </div>
  )
}

function ContextActionButton({
  tooltip,
  disabled,
  variant,
  onClick,
  icon,
  children,
}: {
  tooltip: string
  disabled: boolean
  variant: 'secondary' | 'outline'
  onClick: () => void
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex">
          <Button type="button" variant={variant} size="xs" onClick={onClick} disabled={disabled}>
            {icon}
            {children}
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">{tooltip}</TooltipContent>
    </Tooltip>
  )
}

interface ExtractionChatProps {
  documentId: string
  currentPage: number
  canAddWholeDocument?: boolean
  canAddCurrentPage?: boolean
  contextPayload: ExtractionContextPayload | null
  isWholeDocumentSelected: boolean
  selectedPages: number[]
  selectedBlocks: ExtractionContextBlock[]
  onAddWholeDocument: () => void
  onAddCurrentPage: () => void
  onRemovePage: (pageNumber: number) => void
  onRemoveBlock: (blockId: string) => void
  onClearContext: () => void
  disabled?: boolean
  isProcessing?: boolean
  setIsRunningInference?: (isProcessing: boolean) => void
  activeTag?: string
}

export const ExtractionChat = ({
  documentId,
  currentPage,
  canAddWholeDocument = false,
  canAddCurrentPage = false,
  contextPayload,
  isWholeDocumentSelected,
  selectedPages,
  selectedBlocks,
  onAddWholeDocument,
  onAddCurrentPage,
  onRemovePage,
  onRemoveBlock,
  onClearContext,
  disabled,
  isProcessing,
  setIsRunningInference,
  activeTag,
}: ExtractionChatProps) => {
  const { data: workflows, isLoading: isWorkflowsLoading } = useChatWorkflows()
  const triggerWorkflow = useTriggerWorkflow()
  const queryClient = useQueryClient()

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null)
  const [prompt, setPrompt] = useState('')
  const [workflowToPoll, setWorkflowToPoll] = useState<string | null>(null)

  const selectedWorkflow = useMemo(() => {
    if (!workflows?.length) return null
    if (selectedWorkflowId) {
      const persisted = workflows.find((workflow) => workflow.id === selectedWorkflowId)
      if (persisted) return persisted
    }

    const matchingWorkflow = activeTag
      ? workflows.find((workflow) => workflow.tags?.includes(activeTag))
      : null

    return matchingWorkflow || workflows[0]
  }, [workflows, selectedWorkflowId, activeTag])

  const availableScopes = useMemo(() => selectedWorkflow?.extractionScope || [], [selectedWorkflow])
  const canUseDocumentContext = availableScopes.includes('document')
  const canUsePageContext = availableScopes.includes('page')
  const hasContext = contextPayload !== null
  const isCurrentPageSelected = selectedPages.includes(currentPage)
  const isContextCompatible = useMemo(() => {
    if (!contextPayload) return false
    if (contextPayload.kind === 'document') {
      return availableScopes.includes('document')
    }

    return availableScopes.includes('page')
  }, [availableScopes, contextPayload])

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      if (selectedWorkflow && selectedWorkflow.id !== selectedWorkflowId) {
        setSelectedWorkflowId(selectedWorkflow.id)
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [selectedWorkflow, selectedWorkflowId])

  const { data: workflowStatus } = useWorkflowStatus(workflowToPoll)

  useEffect(() => {
    if (workflowStatus?.status === 'Finished') {
      const frame = requestAnimationFrame(() => {
        setWorkflowToPoll(null)
        setIsRunningInference?.(false)
        toast.success('Extraction updated')
        void queryClient.invalidateQueries({
          queryKey: extractionPagesKeys.documentWithTags(documentId, activeTag),
        })
      })

      return () => cancelAnimationFrame(frame)
    }

    if (workflowStatus?.status === 'Failed') {
      const frame = requestAnimationFrame(() => {
        setWorkflowToPoll(null)
        setIsRunningInference?.(false)
        toast.error('Extraction failed')
      })

      return () => cancelAnimationFrame(frame)
    }
  }, [workflowStatus, setIsRunningInference, queryClient, documentId, activeTag])

  const handlePromptChange = useCallback((event: ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(event.target.value)
  }, [])

  const handleSendMessage = useCallback(async () => {
    if (!selectedWorkflow || !contextPayload || !isContextCompatible) return

    setIsRunningInference?.(true)

    try {
      const result = await triggerWorkflow.mutateAsync({
        id: selectedWorkflow.id,
        payload: buildWorkflowTriggerPayload({
          documentId,
          contextPayload,
          currentPage,
          prompt,
          supportsPrompts: selectedWorkflow.supportPrompts,
        }),
      })

      setWorkflowToPoll(result.workflow_id)
      setPrompt('')
      setIsRunningInference?.(false)
    } catch {
      setIsRunningInference?.(false)
      toast.error('Failed to trigger workflow')
    }
  }, [
    selectedWorkflow,
    contextPayload,
    currentPage,
    documentId,
    isContextCompatible,
    prompt,
    setIsRunningInference,
    triggerWorkflow,
  ])

  const documentContextTooltip = getDocumentContextTooltip(
    canUseDocumentContext,
    isWholeDocumentSelected
  )
  const currentPageTooltip = getCurrentPageTooltip({
    canUsePageContext,
    isWholeDocumentSelected,
    isCurrentPageSelected,
    currentPage,
  })

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-between bg-card focus-within:border-t-2 focus-within:border-blue-500'
      )}
    >
      <div className="flex w-full flex-col gap-1.5 px-4 pt-2 pb-1">
        <div className="flex items-center justify-between gap-3">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground/80">
            Context
          </span>
          <Button
            type="button"
            variant="ghost"
            size="xs"
            className="h-6 px-2 text-muted-foreground"
            onClick={onClearContext}
            disabled={disabled || isProcessing || isWorkflowsLoading || !hasContext}
          >
            Clear all
          </Button>
        </div>

        <ContextSection
          hasContext={hasContext}
          isWholeDocumentSelected={isWholeDocumentSelected}
          selectedPages={selectedPages}
          selectedBlocks={selectedBlocks}
          onClearContext={onClearContext}
          onRemovePage={onRemovePage}
          onRemoveBlock={onRemoveBlock}
        />
      </div>

      <Textarea
        className="max-h-50 min-h-25 w-full max-w-full resize-none overflow-y-auto border-0 bg-transparent px-4 pt-2 pb-2 whitespace-pre-wrap focus-visible:ring-0 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-60"
        placeholder="Ask for changes..."
        disabled={disabled || isProcessing || isWorkflowsLoading}
        value={prompt}
        onChange={handlePromptChange}
      />
      {selectedWorkflow && !selectedWorkflow.supportPrompts && (
        <div className="text-destructive text-sm pt-2 px-2">
          This model does not support prompts. Your input will be ignored.
        </div>
      )}
      <div
        className={cn('flex w-full items-center justify-between gap-2 bg-card px-2 py-2', {
          'pointer-events-none opacity-60': disabled || isWorkflowsLoading,
        })}
        aria-disabled={disabled || isWorkflowsLoading}
      >
        <div className="flex w-full items-center justify-between gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild disabled={disabled || isWorkflowsLoading}>
              <Button variant="secondary" size="xs" title="Select Model">
                {selectedWorkflow?.name || 'Select Model'}
                <ChevronDown className="h-3 w-3 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="min-w-40" align="end">
              {workflows?.map((workflow) => (
                <DropdownMenuItem
                  key={workflow.id}
                  onClick={() => setSelectedWorkflowId(workflow.id)}
                >
                  {workflow.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex items-center gap-2">
            {canAddWholeDocument && (
              <ContextActionButton
                tooltip={documentContextTooltip}
                variant={isWholeDocumentSelected ? 'secondary' : 'outline'}
                onClick={onAddWholeDocument}
                disabled={disabled || isProcessing || isWorkflowsLoading || !canUseDocumentContext}
                icon={<Layers className="mr-1 h-3 w-3" />}
              >
                {isWholeDocumentSelected ? 'Whole document added' : 'Add whole document'}
              </ContextActionButton>
            )}

            {canAddCurrentPage && (
              <ContextActionButton
                tooltip={currentPageTooltip}
                variant={isCurrentPageSelected ? 'secondary' : 'outline'}
                onClick={onAddCurrentPage}
                disabled={
                  disabled ||
                  isProcessing ||
                  isWorkflowsLoading ||
                  isWholeDocumentSelected ||
                  !canUsePageContext
                }
                icon={<File className="mr-1 h-3 w-3" />}
              >
                {isCurrentPageSelected ? `Page ${currentPage} added` : 'Add current page'}
              </ContextActionButton>
            )}
          </div>

          <div className="flex-1" />

          <Button
            size="xs"
            type="button"
            className={cn('size-8 rounded-full', isProcessing ? 'bg-blue-500 text-white' : '')}
            disabled={
              disabled ||
              isWorkflowsLoading ||
              !selectedWorkflow ||
              !hasContext ||
              !isContextCompatible ||
              triggerWorkflow.isPending
            }
            onClick={handleSendMessage}
          >
            {triggerWorkflow.isPending ? (
              <Spinner size="sm" />
            ) : (
              <SendHorizonal className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
