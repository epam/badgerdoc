import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Check, ChevronDown, File, Layers, SendHorizonal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/helpers/utils'
import {
  summarizePromptContext,
  type PromptContextPathInserterRegistration,
} from '@/features/workspace/helpers/extraction-chat-context'
import {
  getCurrentPageTooltip,
  getDocumentContextTooltip,
} from '@/features/workspace/helpers/extraction-chat-action-tooltips'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'
import { useTriggerWorkflow } from '@/shared/api/hooks/use-workflows'
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
          <Button
            type="button"
            variant={variant}
            size="xs"
            onMouseDown={(event) => event.preventDefault()}
            onClick={onClick}
            disabled={disabled}
          >
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
  registerPromptContextInserter: PromptContextPathInserterRegistration
  onAddWholeDocument: () => void
  onAddCurrentPage: () => void
  disabled?: boolean
  isProcessing?: boolean
  setIsRunningInference?: (isProcessing: boolean) => void
  activeTag?: string
  workflowSelection: ChatWorkflowSelection
  onTriggerSuccess?: () => void
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
  registerPromptContextInserter,
  onAddWholeDocument,
  onAddCurrentPage,
  disabled,
  isProcessing,
  setIsRunningInference,
  workflowSelection,
  onTriggerSuccess,
}: ExtractionChatProps) => {
  const triggerWorkflow = useTriggerWorkflow()

  const [hasSuccessFeedback, setHasSuccessFeedback] = useState(false)
  const {
    workflows,
    isWorkflowsLoading,
    selectedWorkflow,
    setSelectedWorkflowId,
    availableScopes,
    canUseDocumentContext,
    canUsePageContext,
  } = workflowSelection
  const contextSummary = useMemo(() => summarizePromptContext(prompt), [prompt])
  const hasContext = contextSummary.hasContext
  const hasPromptText = prompt.trim().length > 0
  const hasSendContent = hasPromptText || hasContext
  const isCurrentPageSelected = selectedPages.includes(currentPage)
  // When no context chips are present the prompt is plain text, which is always valid.
  const isContextCompatible = useMemo(() => {
    if (!hasContext) return true
    if (contextSummary.primaryScope === 'document') {
      return availableScopes.includes('document')
    }

    return availableScopes.includes('page')
  }, [availableScopes, contextSummary.primaryScope, hasContext])

  useEffect(() => {
    if (!hasSuccessFeedback) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      setHasSuccessFeedback(false)
    }, 900)

    return () => window.clearTimeout(timeoutId)
  }, [hasSuccessFeedback])

  const handleSendMessage = useCallback(async () => {
    if (!selectedWorkflow || !hasSendContent || !isContextCompatible) return

    setIsRunningInference?.(true)

    try {
      await triggerWorkflow.mutateAsync({
        id: selectedWorkflow.id,
        payload: buildWorkflowTriggerPayload({
          documentId,
          prompt,
        }),
      })

      onPromptChange('')
      setHasSuccessFeedback(true)
      setIsRunningInference?.(false)
      toast.success('Request sent')
      onTriggerSuccess?.()
    } catch {
      setIsRunningInference?.(false)
      toast.error('Failed to trigger workflow')
    }
  }, [
    selectedWorkflow,
    documentId,
    hasSendContent,
    isContextCompatible,
    onPromptChange,
    onTriggerSuccess,
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
  const isSending = Boolean(isProcessing || triggerWorkflow.isPending)
  const isSendDisabled =
    disabled ||
    isSending ||
    hasSuccessFeedback ||
    isWorkflowsLoading ||
    !selectedWorkflow ||
    !hasSendContent ||
    !isContextCompatible

  return (
    <div className="shadow-soft-top relative z-10 flex flex-col items-center justify-between border-t border-border bg-card">
      <div className="flex w-full flex-col gap-2 px-3 pt-3">
        <div className="shadow-subtle overflow-hidden rounded-2xl border border-border bg-background">
          <PromptContextEditor
            placeholder="Ask for changes..."
            disabled={disabled || isProcessing || isWorkflowsLoading}
            value={prompt}
            onChange={onPromptChange}
            canSubmit={!isSendDisabled}
            onSubmitShortcut={handleSendMessage}
            onRegisterContextInserter={registerPromptContextInserter}
          />
        </div>
        {selectedWorkflow && !selectedWorkflow.supportPrompts && (
          <div className="px-1 text-xs text-muted-foreground">
            Input will be ignored for this model
          </div>
        )}
      </div>
      <div
        className={cn(
          'mt-3 flex w-full items-center justify-between gap-2 border-t border-border/70 bg-card px-3 py-3',
          {
            'pointer-events-none opacity-60': disabled || isWorkflowsLoading,
          }
        )}
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
            className={cn(
              'size-8 rounded-full transition-all duration-200',
              hasSuccessFeedback && 'scale-105 bg-emerald-500 text-white ring-4 ring-emerald-100',
              !hasSuccessFeedback && isSending && 'bg-blue-500 text-white'
            )}
            aria-label="Send prompt"
            disabled={isSendDisabled}
            onClick={handleSendMessage}
          >
            {hasSuccessFeedback ? (
              <span
                role="status"
                aria-label="Request sent"
                className="animate-in zoom-in-50 fade-in-0 duration-300"
              >
                <Check className="h-4 w-4" />
              </span>
            ) : isSending ? (
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
