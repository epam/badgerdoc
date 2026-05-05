import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import { useChatWorkflows } from '@/shared/api/hooks/use-workflows'
import type { WorkflowScope } from '@/shared/api/adapters/types'

export interface ChatWorkflow {
  id: number
  name: string
  tags?: string[]
  extractionScope: WorkflowScope[]
  supportPrompts: boolean
}

export interface ChatWorkflowSelection {
  workflows?: ChatWorkflow[]
  isWorkflowsLoading: boolean
  selectedWorkflowId: number | null
  setSelectedWorkflowId: Dispatch<SetStateAction<number | null>>
  selectedWorkflow: ChatWorkflow | null
  availableScopes: WorkflowScope[]
  canUseDocumentContext: boolean
  canUsePageContext: boolean
}

export function useChatWorkflowSelection({ activeTag }: { activeTag?: string }) {
  const { data: workflows, isLoading: isWorkflowsLoading } = useChatWorkflows()
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null)

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

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      if (selectedWorkflow && selectedWorkflow.id !== selectedWorkflowId) {
        setSelectedWorkflowId(selectedWorkflow.id)
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [selectedWorkflow, selectedWorkflowId])

  const availableScopes = useMemo(() => selectedWorkflow?.extractionScope || [], [selectedWorkflow])

  return {
    workflows,
    isWorkflowsLoading,
    selectedWorkflowId,
    setSelectedWorkflowId,
    selectedWorkflow,
    availableScopes,
    canUseDocumentContext: availableScopes.includes('document'),
    canUsePageContext: availableScopes.includes('page'),
  } satisfies ChatWorkflowSelection
}
