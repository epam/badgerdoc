import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, useSearch, useMatches } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { SplitView } from '@/design-system/patterns/split-view'
import { DocumentHeader } from '@/components/document-header'
import { DocumentHierarchyPopover } from '@/components/document-hierarchy-popover'
import { AGENT_TAB_ID, WorkspaceTabs } from './components/workspace-tabs.tsx'
import { CollectionViewer } from '@/components/collection-viewer/collection-viewer'
import { Button } from '@/components/ui/button'
import { TaskNotFoundPage, DocumentNotFoundPage } from '@/components/not-found'
import { APIError } from '@/shared/api/client'
import {
  useWorkspaceDocument,
  useTask,
  useBadgerDocExtractionPages,
  useTags,
} from '@/shared/api/hooks'
import { useTasksQueue } from '@/shared/api/hooks/use-tasks'
import { useExtractionState } from '@/features/workspace/hooks/use-extraction-state'
import { useExtractionApi } from '@/features/workspace/hooks/use-extraction-api'
import { useReloadDraftAutosave } from '@/features/workspace/hooks/use-reload-draft-autosave'
import { useExtractionChatContext } from '@/features/workspace/hooks/use-extraction-chat-context'
import { useChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'
import { useViewerChatContext } from '@/features/workspace/hooks/use-viewer-chat-context'
import { WorkspaceLoadingSkeleton } from '@/features/workspace/components/workspace-loading-skeleton.tsx'
import {
  TaskFiltersSearch,
  taskFiltersFromSearch,
  taskFiltersToSearch,
} from '@/helpers/task-filters-search'
import { ExtractionResultsTab } from '@/features/workspace/components/extraction-results-tab.tsx'
import { DocumentOverviewPopover } from '@/features/workspace/components/document-overview-popover'
import { NoExtractionTagsEmptyState } from '@/features/workspace/components/no-extraction-tags-empty-state'
import { AgentLogsTab } from '@/features/workspace/components/agent-logs-tab'
import { agentLogsKeys } from '@/shared/api/hooks/use-agent-logs'
import type { BadgerDocDocument } from '@/shared/api/badgerdoc/types'

export function WorkspacePage() {
  // Support both /tasks/$taskId and legacy /document/$id routes
  const params = useParams({ strict: false }) as { id?: string; taskId?: string }
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const search = useSearch({ strict: false }) as { tag?: string } & TaskFiltersSearch
  const matches = useMatches()

  const currentRoute = useMemo(() => {
    const lastMatch = matches[matches.length - 1]
    if (lastMatch?.routeId === '/tasks/$taskId') {
      return 'tasks'
    } else if (lastMatch?.routeId === '/documents/$id') {
      return 'documents'
    }
    return 'unknown'
  }, [matches])

  // Get taskId from URL params (primary route is /tasks/$taskId)
  const taskId = params.taskId ? Number(params.taskId) : undefined

  // Fetch task details to get document info and current status
  const {
    data: taskData,
    isLoading: taskLoading,
    isError: taskError,
    error: taskErrorData,
  } = useTask(taskId ?? 0)

  // Derive documentId from task data (task.document.id) or from legacy URL param
  const documentId = taskData?.document?.id ? String(taskData.document.id) : (params.id ?? '')
  const currentStatusId = taskData?.status?.id ?? 0

  // Fetch extraction tags (dynamic tabs)
  const { data: extractionTags, isLoading: tagsLoading } = useTags()

  const orderedExtractionTags = useMemo(
    () => [...(extractionTags ?? [])].sort((a, b) => (a.order || 0) - (b.order || 0)),
    [extractionTags]
  )
  const requestedTab = search.tag === 'overview' ? undefined : search.tag
  const activeTab = requestedTab || AGENT_TAB_ID
  const isAgentTab = activeTab === AGENT_TAB_ID
  const hasExtractionTags = orderedExtractionTags.length > 0
  const taskFilters = useMemo(() => taskFiltersFromSearch(search), [search])
  const taskFiltersSearch = useMemo(() => taskFiltersToSearch(taskFilters), [taskFilters])

  // Strip legacy ?tag=overview from the URL so it doesn't linger in bookmarks
  useEffect(() => {
    if (search.tag !== 'overview') return
    const rest = { ...search }
    delete rest.tag
    void navigate({
      to: '.',
      search: rest,
      replace: true,
    })
  }, [search, navigate])

  // Use extraction tab IDs directly as tag names for API calls (tags have hyphens, not spaces).
  const activeTagName = !isAgentTab && activeTab ? activeTab : undefined

  const { data: extractionPages, isLoading: extractionLoading } = useBadgerDocExtractionPages(
    documentId,
    activeTagName,
    Boolean(activeTagName)
  )
  const extractionResultsLoading = tagsLoading || extractionLoading

  // Fetch document data
  const {
    data: document,
    isLoading: documentLoading,
    isError: documentError,
    error: documentErrorData,
  } = useWorkspaceDocument(documentId?.toString() || '')
  const { data: queue, isLoading: isLoadingTasks } = useTasksQueue({
    currentTaskId: currentRoute === 'tasks' && taskId ? taskId : -1,
    filters: taskFilters,
  })

  const taskStatusName = taskData?.status?.name

  const [isEditMode, setIsEditMode] = useState(false)
  const [isRunningInference, setIsRunningInference] = useState(false)
  const canUseEditingMode = Boolean(activeTagName)
  const {
    currentPage,
    setCurrentPage,
    activeBlockId,
    setActiveBlockId,
    hasChanges,
    highlights,
    pendingPayload,
    onBaselineReady,
    onContentChange,
    onBlockDelete,
    revertChanges,
    acceptChanges,
    scopedExtractionPages,
    handleBlockBoundingBoxUpdate,
    handleBlockCreate,
    createdBlockIds,
    deletedBlockIds,
  } = useExtractionState({
    extractionPages,
    activeTag: activeTagName,
  })
  const {
    prompt,
    isWholeDocumentSelected,
    selectedPages,
    selectedBlocks,
    setPrompt,
    registerPromptContextInserter,
    addWholeDocument,
    togglePage,
    toggleBlock,
    removeBlocks,
  } = useExtractionChatContext({
    documentId,
    extractionPages: scopedExtractionPages,
  })
  const workflowSelection = useChatWorkflowSelection({
    activeTag: activeTagName,
  })

  const {
    saveExtractionPages,
    acceptExtraction,
    isPending: isApiPending,
  } = useExtractionApi({
    documentId,
    activeTag: activeTagName,
  })

  const handleSaveExtraction = useCallback(async () => {
    if (!pendingPayload?.length) return
    await saveExtractionPages(pendingPayload)
  }, [pendingPayload, saveExtractionPages])

  const handleAcceptClick = useCallback(async () => {
    if (!pendingPayload?.length) return

    const deletedBlockIdsToPrune = deletedBlockIds

    const acceptedExtraction = await acceptExtraction(pendingPayload)
    acceptChanges(pendingPayload, acceptedExtraction?.id ?? null)
    removeBlocks(deletedBlockIdsToPrune)
    setIsEditMode(false)
  }, [acceptChanges, acceptExtraction, deletedBlockIds, pendingPayload, removeBlocks])

  useReloadDraftAutosave({
    documentId,
    activeTagName,
    hasChanges,
    pendingPayload,
    onRestoreDraft: acceptExtraction,
  })

  const handleRevertClick = useCallback(() => {
    revertChanges()
    setActiveBlockId(null)
    setIsEditMode(false)
  }, [revertChanges, setActiveBlockId])

  const handleToggleBlockContext = useCallback(
    (blockId: string, pageNumber: number | null) => {
      if (pageNumber === null) return
      toggleBlock({ blockId, pageNumber })
    },
    [toggleBlock]
  )

  const handleAddCurrentPage = useCallback(() => {
    togglePage(currentPage)
  }, [togglePage, currentPage])

  const handleBlockDelete = useCallback(
    (blockId: string, pageNumber: number | null) => {
      onBlockDelete(blockId, pageNumber)
    },
    [onBlockDelete]
  )

  const chatContext = useMemo(
    () => ({
      prompt,
      isWholeDocumentSelected,
      selectedPages,
      selectedBlocks,
      onPromptChange: setPrompt,
      registerPromptContextInserter,
      onAddWholeDocument: addWholeDocument,
      onAddCurrentPage: handleAddCurrentPage,
      onToggleBlock: handleToggleBlockContext,
    }),
    [
      prompt,
      isWholeDocumentSelected,
      selectedPages,
      selectedBlocks,
      setPrompt,
      registerPromptContextInserter,
      addWholeDocument,
      handleAddCurrentPage,
      handleToggleBlockContext,
    ]
  )

  const pageChatContext = useViewerChatContext({
    canAddContext: Boolean(activeTagName),
    currentPage,
    selectedPages,
    isWholeDocumentSelected,
    isContextInteractionDisabled:
      extractionResultsLoading || hasChanges || isApiPending || isRunningInference,
    workflowSelection,
    onAddWholeDocument: addWholeDocument,
    onAddCurrentPage: handleAddCurrentPage,
  })

  const handleTabChange = useCallback(
    (tab: string) => {
      setIsEditMode(false)
      setActiveBlockId(null)

      // Navigation updates URL which updates activeTab (derived from search.tag).
      const routes = {
        tasks: {
          to: '/tasks/$taskId',
          params: { taskId: String(taskId) },
        },
        documents: {
          to: '/documents/$id',
          params: { id: String(documentId) },
        },
      } as const

      if (currentRoute in routes) {
        const nextSearch =
          currentRoute === 'tasks'
            ? { ...taskFiltersSearch, ...(tab ? { tag: tab } : {}) }
            : { ...(tab ? { tag: tab } : {}) }

        void navigate({
          ...routes[currentRoute as keyof typeof routes],
          search: nextSearch,
          replace: true,
        })
      }
    },
    [navigate, taskId, currentRoute, documentId, taskFiltersSearch, setActiveBlockId]
  )

  const handleContextualRequestSuccess = useCallback(() => {
    handleTabChange(AGENT_TAB_ID)
    void queryClient.invalidateQueries({
      queryKey: agentLogsKeys.list({ documentId, page: 1 }),
    })
  }, [documentId, handleTabChange, queryClient])

  const handlePrevious = useCallback(() => {
    void navigate({
      to: '/tasks/$taskId',
      params: { taskId: `${queue?.prevId}` },
      search: {
        ...taskFiltersSearch,
        ...(activeTab ? { tag: activeTab } : {}),
      },
      replace: true,
    })
  }, [navigate, queue?.prevId, taskFiltersSearch, activeTab])

  const handleNext = useCallback(() => {
    void navigate({
      to: '/tasks/$taskId',
      params: { taskId: `${queue?.nextId}` },
      search: {
        ...taskFiltersSearch,
        ...(activeTab ? { tag: activeTab } : {}),
      },
      replace: true,
    })
  }, [navigate, queue?.nextId, taskFiltersSearch, activeTab])

  const handleHierarchyDocumentSelect = useCallback(
    (selectedDocument: BadgerDocDocument) => {
      if (String(selectedDocument.id) === String(documentId)) {
        return
      }

      void navigate({
        to: '/documents/$id',
        params: { id: String(selectedDocument.id) },
        search: activeTab ? { tag: activeTab } : {},
      })
    },
    [activeTab, documentId, navigate]
  )

  // Show 404 page when task or document is not found
  const isTask404 = taskId && taskError && (taskErrorData as APIError)?.statusCode === 404
  const isDocument404 = documentError && (documentErrorData as APIError)?.statusCode === 404

  if (isTask404) {
    return <TaskNotFoundPage id={taskId} />
  }

  if (isDocument404) {
    return <DocumentNotFoundPage id={documentId} />
  }

  // Show loading skeleton while data is fetching
  // When using /tasks/$taskId route, wait for task data to load first
  if (taskLoading || (taskId && !taskData) || documentLoading || !document) {
    return <WorkspaceLoadingSkeleton />
  }

  // Prepare document data for components
  const documentForHeader = {
    title: document.title,
    type: document.type,
    authors: document.authors,
    date: document.publicationDate || document.createdAt.split('T')[0],
  }
  const documentForHierarchy = {
    id: document.id,
    uploaded_by: document.uploadedBy,
    parent_document_id: document.parentDocumentId ?? null,
    file: document.pdfUrl,
    metadata: document.metadata,
    tags: document.tags,
    created_at: document.createdAt,
    updated_at: document.updatedAt,
    name: document.title,
    status: document.status,
  } satisfies BadgerDocDocument

  const documentForOverview = {
    id: document.id,
    title: document.title,
    type: document.type,
    metadata: document.metadata,
    tags: document.tags,
    uploadedBy: document.uploadedBy,
    abstract: document.abstract,
    authors: document.authors,
    publicationDate: document.publicationDate,
  }
  const viewerHighlights = highlights

  const renderTabContent = () => {
    if (isAgentTab) {
      return (
        <AgentLogsTab
          documentId={documentId}
          currentPage={currentPage}
          chatContext={chatContext}
          workflowSelection={workflowSelection}
          isRunningInference={isRunningInference}
          setIsRunningInference={setIsRunningInference}
          onTriggerSuccess={handleContextualRequestSuccess}
        />
      )
    }

    if (!tagsLoading && !hasExtractionTags) {
      return <NoExtractionTagsEmptyState />
    }

    return (
      <ExtractionResultsTab
        isLoading={extractionResultsLoading}
        extractionPages={scopedExtractionPages}
        tag={activeTab || 'extraction results'}
        hasUnsavedChanges={hasChanges}
        onBaselineReady={onBaselineReady}
        onContentChange={onContentChange}
        onSaveExtraction={handleSaveExtraction}
        onRevertChanges={handleRevertClick}
        onAcceptChanges={handleAcceptClick}
        onBlockDelete={handleBlockDelete}
        isSaving={isApiPending}
        activeBlockId={activeBlockId}
        onBlockSelect={setActiveBlockId}
        onPageNavigate={setCurrentPage}
        currentPage={currentPage}
        documentId={documentId}
        chatContext={chatContext}
        workflowSelection={workflowSelection}
        isRunningInference={isRunningInference}
        setIsRunningInference={setIsRunningInference}
        onTriggerSuccess={handleContextualRequestSuccess}
      />
    )
  }

  return (
    <div className="flex h-[calc(100vh-1.5rem)] flex-col">
      <DocumentHeader
        documentId={documentId}
        title={documentForHeader.title}
        authors={documentForHeader.authors}
        date={documentForHeader.date}
        statusName={taskStatusName}
        backLink="/tasks"
        backSearch={taskFiltersSearch as Record<string, unknown>}
        backLabel="Back"
        useSmartBack
        titleActions={
          <div className="flex min-w-0 items-center gap-2">
            <DocumentHierarchyPopover
              currentDocument={documentForHierarchy}
              onDocumentSelect={handleHierarchyDocumentSelect}
            />
            <DocumentOverviewPopover document={documentForOverview} />
          </div>
        }
      >
        {currentRoute === 'tasks' && !isLoadingTasks && queue && (
          <>
            {queue.position !== undefined && queue.total !== undefined && (
              <span className="text-sm text-muted-foreground">
                {queue.position} / {queue.total}
              </span>
            )}
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={handlePrevious}
                disabled={!queue.prevId}
                className="h-8 w-8"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleNext}
                disabled={!queue.nextId}
                className="h-8 w-8"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </>
        )}
      </DocumentHeader>

      <div className="flex-1 overflow-hidden">
        <SplitView
          left={
            <CollectionViewer
              documentId={documentId?.toString() || ''}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              onHighlightClick={(highlightId) => setActiveBlockId(highlightId)}
              activeHighlightId={activeBlockId}
              highlights={viewerHighlights}
              isEditMode={canUseEditingMode && isEditMode}
              canUseEditMode={canUseEditingMode}
              onToggleEditMode={() => {
                if (!canUseEditingMode) return
                setIsEditMode((prev) => !prev)
              }}
              onHighlightUpdate={handleBlockBoundingBoxUpdate}
              onHighlightCreate={handleBlockCreate}
              createdHighlightIds={createdBlockIds}
              pageChatContext={pageChatContext}
            />
          }
          right={
            <div className="flex h-full flex-col">
              <WorkspaceTabs
                activeTab={activeTab}
                onTabChange={handleTabChange}
                extractionTags={orderedExtractionTags}
                isLoadingTags={tagsLoading}
                currentStatusId={taskId ? currentStatusId : undefined}
                currentStatusName={taskId ? taskStatusName : undefined}
              />
              <div className="flex-1 overflow-hidden">{renderTabContent()}</div>
            </div>
          }
          defaultRatio={0.5}
        />
      </div>
    </div>
  )
}
