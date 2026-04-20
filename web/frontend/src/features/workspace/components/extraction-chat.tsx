import { useCallback, useMemo, useState, ChangeEvent, useEffect } from 'react'
import { ChevronDown, SendHorizonal, Layers, File } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/helpers/utils'
import { toast } from 'sonner'
import {
  useChatWorkflows,
  useTriggerWorkflow,
  useWorkflowStatus,
} from '@/shared/api/hooks/use-workflows'
import { WorkflowScope } from '@/shared/api/adapters/types'
import { useQueryClient } from '@tanstack/react-query'
import { extractionPagesKeys } from '@/shared/api/hooks/use-badgerdoc-extraction-pages'
import { Spinner } from '@/components/ui/spinner'

interface ExtractionChatProps {
  documentId: string
  currentPage: number
  disabled?: boolean
  isProcessing?: boolean
  setIsRunningInference?: (isProcessing: boolean) => void
  activeTag?: string
}

export const ExtractionChat = ({
  documentId,
  currentPage,
  disabled,
  isProcessing,
  setIsRunningInference,
  activeTag,
}: ExtractionChatProps) => {
  const { data: workflows, isLoading: isWorkflowsLoading } = useChatWorkflows()
  const triggerWorkflow = useTriggerWorkflow()
  const queryClient = useQueryClient()

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null)
  const [currentScope, setCurrentScope] = useState<WorkflowScope | null>(null)
  const [prompt, setPrompt] = useState<string>('')
  const [workflowToPoll, setWorkflowToPoll] = useState<string | null>(null)

  const selectedWorkflow = useMemo(() => {
    if (!workflows?.length) return null
    if (selectedWorkflowId) {
      const persisted = workflows.find((w) => w.id === selectedWorkflowId)
      if (persisted) return persisted
    }
    const matchingWorkflow = activeTag ? workflows.find((w) => w.tags?.includes(activeTag)) : null
    return matchingWorkflow || workflows[0]
  }, [workflows, selectedWorkflowId, activeTag])

  const availableScopes = useMemo(() => selectedWorkflow?.extractionScope || [], [selectedWorkflow])

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      // Sync selectedWorkflowId
      if (selectedWorkflow && selectedWorkflow.id !== selectedWorkflowId) {
        setSelectedWorkflowId(selectedWorkflow.id)
      }

      // Sync currentScope
      if (currentScope && !availableScopes.includes(currentScope)) {
        setCurrentScope(availableScopes[0] ?? null)
      } else if (!currentScope && availableScopes.length > 0) {
        setCurrentScope(availableScopes[0])
      }
    })
    return () => cancelAnimationFrame(frame)
  }, [selectedWorkflow, selectedWorkflowId, availableScopes, currentScope])

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
    } else if (workflowStatus?.status === 'Failed') {
      const frame = requestAnimationFrame(() => {
        setWorkflowToPoll(null)
        setIsRunningInference?.(false)
        toast.error('Extraction failed')
      })
      return () => cancelAnimationFrame(frame)
    }
  }, [workflowStatus, setIsRunningInference, queryClient, documentId, activeTag])

  const handlePromptChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value)
  }, [])

  const handleSendMessage = useCallback(async () => {
    if (!selectedWorkflow || !currentScope) return

    setIsRunningInference?.(true)
    try {
      const payload: Record<string, unknown> = {
        document_id: Number(documentId),
        prompt: selectedWorkflow.supportPrompts ? prompt : undefined,
      }

      if (currentScope === 'page') {
        payload.scope = 'page'
        payload.page_number = currentPage
      } else {
        payload.scope = 'document'
      }

      const result = await triggerWorkflow.mutateAsync({
        id: selectedWorkflow.id,
        payload,
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
    currentScope,
    documentId,
    prompt,
    currentPage,
    triggerWorkflow,
    setIsRunningInference,
  ])

  const ScopeIcon = useMemo(() => {
    if (currentScope === 'page') return File
    return Layers
  }, [currentScope])

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-between bg-card focus-within:border-t-2 focus-within:border-blue-500'
      )}
    >
      <Textarea
        className="max-h-85 min-h-16 w-full max-w-full resize-none overflow-y-auto border-0 bg-transparent px-4 pt-4 pb-2 whitespace-pre-wrap focus-visible:ring-0 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-60"
        placeholder="Ask for changes..."
        disabled={disabled || isProcessing || isWorkflowsLoading}
        value={prompt}
        onChange={handlePromptChange}
      />
      {!selectedWorkflow?.supportPrompts && (
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

          <DropdownMenu>
            <DropdownMenuTrigger asChild disabled={disabled || isWorkflowsLoading}>
              <Button
                variant={currentScope ? 'secondary' : 'outline'}
                size="xs"
                title="Select scope"
              >
                {currentScope && <ScopeIcon className="mr-1 h-3 w-3" />}
                {!currentScope
                  ? 'Select Scope'
                  : currentScope === 'page'
                    ? `Page ${currentPage}`
                    : 'Whole Document'}
                <ChevronDown className="h-3 w-3 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-40">
              {availableScopes.includes('document') && (
                <DropdownMenuItem
                  onClick={() => setCurrentScope('document')}
                  className="flex items-center gap-2 text-xs"
                >
                  <Layers className="h-3 w-3" />
                  Whole document
                </DropdownMenuItem>
              )}
              {availableScopes.includes('page') && (
                <DropdownMenuItem
                  onClick={() => setCurrentScope('page')}
                  className="flex items-center gap-2 text-xs"
                >
                  <File className="h-3 w-3" />
                  Current Page
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex-1"></div>

          <Button
            size="xs"
            type="button"
            className={cn('size-8 rounded-full', isProcessing ? 'bg-blue-500 text-white' : '')}
            disabled={
              disabled ||
              isWorkflowsLoading ||
              !selectedWorkflow ||
              !currentScope ||
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
