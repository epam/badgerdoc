import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ChevronDown, File, Layers, SendHorizonal } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/helpers/utils'
import { summarizePromptContext } from '@/features/workspace/helpers/extraction-chat-context'
import { extractionPagesKeys } from '@/shared/api/hooks/use-badgerdoc-extraction-pages'
import {
  useChatWorkflows,
  useTriggerWorkflow,
  useWorkflowStatus,
} from '@/shared/api/hooks/use-workflows'
import { Spinner } from '@/components/ui/spinner'
import { toast } from 'sonner'
import { PromptContextEditor } from './prompt-context-editor'

function buildWorkflowTriggerPayload({
  documentId,
  prompt,
}: {
  documentId: string
  prompt: string
}) {
  return {
    document_id: Number(documentId),
    llm_params: prompt,
  } satisfies Record<string, unknown>
}

function getDocumentContextTooltip(
  canUseDocumentContext: boolean,
  isWholeDocumentSelected: boolean
) {
  if (!canUseDocumentContext) {
    return 'Whole document is not available for this workflow'
  }

  return isWholeDocumentSelected ? 'Add another whole document reference' : 'Add whole document'
}

function getCurrentPageTooltip({
  canUsePageContext,
  isCurrentPageSelected,
  currentPage,
}: {
  canUsePageContext: boolean
  isCurrentPageSelected: boolean
  currentPage: number
}) {
  if (!canUsePageContext) {
    return 'Current page context is not available for this workflow'
  }

  return isCurrentPageSelected ? `Add another Page ${currentPage} reference` : 'Add current page'
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
  prompt: string
  isWholeDocumentSelected: boolean
  selectedPages: number[]
  onPromptChange: (prompt: string) => void
  onAddWholeDocument: () => void
  onAddCurrentPage: () => void
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
  prompt,
  isWholeDocumentSelected,
  selectedPages,
  onPromptChange,
  onAddWholeDocument,
  onAddCurrentPage,
  disabled,
  isProcessing,
  setIsRunningInference,
  activeTag,
}: ExtractionChatProps) => {
  const { data: workflows, isLoading: isWorkflowsLoading } = useChatWorkflows()
  const triggerWorkflow = useTriggerWorkflow()
  const queryClient = useQueryClient()

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null)
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
  const contextSummary = useMemo(() => summarizePromptContext(prompt), [prompt])
  const hasContext = contextSummary.hasContext
  const isCurrentPageSelected = selectedPages.includes(currentPage)
  const isContextCompatible = useMemo(() => {
    if (!hasContext) return false
    if (contextSummary.primaryScope === 'document') {
      return availableScopes.includes('document')
    }

    return availableScopes.includes('page')
  }, [availableScopes, contextSummary.primaryScope, hasContext])

  useEffect(() => {
    // Defer to next frame to avoid setState during React's render phase
    // when selectedWorkflow is derived from workflows list on first load.
    const frame = requestAnimationFrame(() => {
      if (selectedWorkflow && selectedWorkflow.id !== selectedWorkflowId) {
        setSelectedWorkflowId(selectedWorkflow.id)
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [selectedWorkflow, selectedWorkflowId])

  const { data: workflowStatus } = useWorkflowStatus(workflowToPoll)

  useEffect(() => {
    // Defer state cleanup and side effects (toast, cache invalidation) to
    // avoid triggering them synchronously inside the polling render cycle.
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

  const handleSendMessage = useCallback(async () => {
    if (!selectedWorkflow || !hasContext || !isContextCompatible) return

    setIsRunningInference?.(true)

    try {
      const result = await triggerWorkflow.mutateAsync({
        id: selectedWorkflow.id,
        payload: buildWorkflowTriggerPayload({
          documentId,
          prompt,
        }),
      })

      setWorkflowToPoll(result.workflow_id)
      onPromptChange('')
    } catch {
      setIsRunningInference?.(false)
      toast.error('Failed to trigger workflow')
    }
  }, [
    selectedWorkflow,
    documentId,
    hasContext,
    isContextCompatible,
    onPromptChange,
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
    isCurrentPageSelected,
    currentPage,
  })

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-between bg-card focus-within:border-t-2 focus-within:border-blue-500'
      )}
    >
      <PromptContextEditor
        placeholder="Ask for changes..."
        disabled={disabled || isProcessing || isWorkflowsLoading}
        value={prompt}
        onChange={onPromptChange}
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
                Add whole document
              </ContextActionButton>
            )}

            {canAddCurrentPage && (
              <ContextActionButton
                tooltip={currentPageTooltip}
                variant={isCurrentPageSelected ? 'secondary' : 'outline'}
                onClick={onAddCurrentPage}
                disabled={disabled || isProcessing || isWorkflowsLoading || !canUsePageContext}
                icon={<File className="mr-1 h-3 w-3" />}
              >
                Add current page
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
