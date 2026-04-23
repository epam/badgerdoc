import { useCallback, useMemo, useState } from 'react'
import { useParams, useNavigate, useSearch, useMatches } from '@tanstack/react-router'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { SplitView } from '@/design-system/patterns/split-view'
import { DocumentHeader } from '@/components/document-header'
import { WorkspaceTabs } from './components/workspace-tabs.tsx'
import { CollectionViewer } from '@/components/collection-viewer/collection-viewer'
import { Button } from '@/components/ui/button'
import { OverviewTab } from './components/overview-tab.tsx'
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
import { WorkspaceLoadingSkeleton } from '@/features/workspace/components/workspace-loading-skeleton.tsx'
import {
  TaskFiltersSearch,
  taskFiltersFromSearch,
  taskFiltersToSearch,
} from '@/helpers/task-filters-search'
import { ExtractionResultsTab } from '@/features/workspace/components/extraction-results-tab.tsx'

export function WorkspacePage() {
  // Support both /tasks/$taskId and legacy /document/$id routes
  const params = useParams({ strict: false }) as { id?: string; taskId?: string }
  const navigate = useNavigate()
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

  // Derive activeTab from URL search params
  const activeTab = search.tag || 'overview'
  const taskFilters = useMemo(() => taskFiltersFromSearch(search), [search])
  const taskFiltersSearch = useMemo(() => taskFiltersToSearch(taskFilters), [taskFilters])

  // Use activeTab directly as tag name for API calls (tags have hyphens, not spaces)
  const activeTagName = activeTab === 'overview' ? undefined : activeTab

  const { data: extractionPages, isLoading: extractionLoading } = useBadgerDocExtractionPages(
    documentId,
    activeTagName
  )

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
  const isOverviewTab = activeTab === 'overview'
  const canUseEditingMode = !isOverviewTab
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
    addWholeDocument,
    togglePage,
    toggleBlock,
    removeBlock,
  } = useExtractionChatContext({
    documentId,
    extractionPages: scopedExtractionPages,
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

    await acceptExtraction(pendingPayload)
    acceptChanges(pendingPayload)
    setIsEditMode(false)
  }, [acceptChanges, acceptExtraction, pendingPayload])

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
      removeBlock(blockId)
    },
    [onBlockDelete, removeBlock]
  )

  const chatContext = useMemo(
    () => ({
      prompt,
      isWholeDocumentSelected,
      selectedPages,
      selectedBlocks,
      onPromptChange: setPrompt,
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
      addWholeDocument,
      handleAddCurrentPage,
      handleToggleBlockContext,
    ]
  )

  const pageChatContext = useMemo(
    () => ({
      canAddCurrentPageToContext: !isOverviewTab,
      isCurrentPageInContext: selectedPages.includes(currentPage),
      isCurrentPageContextDisabled: false,
      currentPageContextTooltip: selectedPages.includes(currentPage)
        ? `Add another Page ${currentPage} reference`
        : undefined,
      onAddCurrentPageToContext: handleAddCurrentPage,
    }),
    [isOverviewTab, selectedPages, currentPage, handleAddCurrentPage]
  )

  const handleTabChange = useCallback(
    (tab: string) => {
      setIsEditMode(false)
      setActiveBlockId(null)

      // Navigation updates URL which updates activeTab (derived from search.tag)
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
            ? { ...taskFiltersSearch, ...(tab !== 'overview' ? { tag: tab } : {}) }
            : { ...(tab !== 'overview' ? { tag: tab } : {}) }

        void navigate({
          ...routes[currentRoute as keyof typeof routes],
          search: nextSearch,
          replace: true,
        })
      }
    },
    [navigate, taskId, currentRoute, documentId, taskFiltersSearch, setActiveBlockId]
  )

  const handlePrevious = useCallback(() => {
    void navigate({
      to: '/tasks/$taskId',
      params: { taskId: `${queue?.prevId}` },
      search: {
        ...taskFiltersSearch,
        ...(activeTab !== 'overview' ? { tag: activeTab } : {}),
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
        ...(activeTab !== 'overview' ? { tag: activeTab } : {}),
      },
      replace: true,
    })
  }, [navigate, queue?.nextId, taskFiltersSearch, activeTab])

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
  const viewerHighlights = activeTab === 'overview' ? {} : highlights

  const renderTabContent = () => {
    // Special case: Overview tab (hardcoded)
    if (activeTab === 'overview') {
      return <OverviewTab document={documentForOverview} />
    }

    return (
      <ExtractionResultsTab
        isLoading={extractionLoading}
        extractionPages={scopedExtractionPages}
        tag={activeTab}
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
                extractionTags={extractionTags}
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
