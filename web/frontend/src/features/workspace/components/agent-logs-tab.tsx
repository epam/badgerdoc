import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { AlertCircle, Bot } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import type { AgentLog } from '@/shared/api/badgerdoc/types'
import { fetchAgentLogs, mergeAgentLogs, useAgentLogs } from '@/shared/api/hooks/use-agent-logs'
import type { ExtractionChatContextProps } from '@/features/workspace/helpers/extraction-chat-context'
import type { ChatWorkflowSelection } from '@/features/workspace/hooks/use-chat-workflow-selection'
import { ExtractionChat } from '@/features/workspace/components/extraction-chat'
import { AgentLogEntry } from './agent-log-entry'

const AGENT_LOG_POLLING_INTERVAL_MS = 2500
const OLDER_LOG_SCROLL_THRESHOLD_PX = 64
const BOTTOM_SCROLL_THRESHOLD_PX = 100

interface AgentLogsTabProps {
  documentId: string
  currentPage: number
  chatContext: ExtractionChatContextProps
  workflowSelection: ChatWorkflowSelection
  isRunningInference: boolean
  setIsRunningInference: (isProcessing: boolean) => void
  onTriggerSuccess?: () => void
}

function AgentLogsLoadingState() {
  return (
    <div className="space-y-3 p-4" aria-label="Loading agent logs">
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
    </div>
  )
}

function AgentLogsEmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <Bot className="mb-4 h-12 w-12 text-muted-foreground" aria-hidden="true" />
      <h3 className="text-lg font-medium">No agent logs yet</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Agent workflow activity will appear here when logs are available.
      </p>
    </div>
  )
}

function AgentLogsErrorState() {
  return (
    <div
      className="m-4 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"
      role="alert"
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>Failed to load agent logs.</span>
    </div>
  )
}

export function AgentLogsTab({
  documentId,
  currentPage,
  chatContext,
  workflowSelection,
  isRunningInference,
  setIsRunningInference,
  onTriggerSuccess,
}: AgentLogsTabProps) {
  const { data, isLoading, isError } = useAgentLogs({
    documentId,
    page: 1,
  })
  const [logs, setLogs] = useState<AgentLog[]>([])
  const [hasPollingError, setHasPollingError] = useState(false)
  const [nextOlderPage, setNextOlderPage] = useState<number | null>(null)
  const [hasMoreOlderLogs, setHasMoreOlderLogs] = useState(false)
  const [isLoadingOlder, setIsLoadingOlder] = useState(false)
  const isPollingRef = useRef(false)
  const isLoadingOlderRef = useRef(false)
  const scrollContainerRef = useRef<HTMLDivElement | null>(null)
  const pendingScrollRestoreRef = useRef<{ scrollHeight: number; scrollTop: number } | null>(null)
  const pendingScrollToBottomRef = useRef(false)
  const latestCreatedAtRef = useRef<string | null>(null)

  const scrollToBottom = useCallback(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    scrollContainer.scrollTop = scrollContainer.scrollHeight
  }, [])

  const isNearBottom = useCallback(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return true

    return (
      scrollContainer.scrollHeight - scrollContainer.scrollTop - scrollContainer.clientHeight <
      BOTTOM_SCROLL_THRESHOLD_PX
    )
  }, [])

  useEffect(() => {
    setLogs([])
    setHasPollingError(false)
    setNextOlderPage(null)
    setHasMoreOlderLogs(false)
    setIsLoadingOlder(false)
    isLoadingOlderRef.current = false
    latestCreatedAtRef.current = null
    pendingScrollRestoreRef.current = null
    pendingScrollToBottomRef.current = true
  }, [documentId])

  useEffect(() => {
    if (!data) return
    pendingScrollToBottomRef.current = true
    setLogs(data.results)
    latestCreatedAtRef.current = data.results.at(-1)?.created_at ?? null
    setHasPollingError(false)
    setNextOlderPage(data.next ? 2 : null)
    setHasMoreOlderLogs(Boolean(data.next))
  }, [data])

  useLayoutEffect(() => {
    const scrollContainer = scrollContainerRef.current
    const pendingRestore = pendingScrollRestoreRef.current
    if (!scrollContainer) return

    if (pendingRestore) {
      const scrollHeightDelta = scrollContainer.scrollHeight - pendingRestore.scrollHeight
      scrollContainer.scrollTop = pendingRestore.scrollTop + scrollHeightDelta
      pendingScrollRestoreRef.current = null
      pendingScrollToBottomRef.current = false
      return
    }

    if (!pendingScrollToBottomRef.current) return

    scrollToBottom()
    pendingScrollToBottomRef.current = false
  }, [logs, scrollToBottom])

  const loadOlderLogs = useCallback(async () => {
    if (!documentId || !nextOlderPage || !hasMoreOlderLogs || isLoadingOlderRef.current) return

    const scrollContainer = scrollContainerRef.current
    isLoadingOlderRef.current = true
    setIsLoadingOlder(true)

    if (scrollContainer) {
      pendingScrollRestoreRef.current = {
        scrollHeight: scrollContainer.scrollHeight,
        scrollTop: scrollContainer.scrollTop,
      }
    }

    try {
      const response = await fetchAgentLogs({ documentId, page: nextOlderPage })
      setLogs((currentLogs) => mergeAgentLogs(currentLogs, response.results))
      setHasMoreOlderLogs(Boolean(response.next))
      setNextOlderPage(response.next ? nextOlderPage + 1 : null)
    } catch {
      pendingScrollRestoreRef.current = null
    } finally {
      isLoadingOlderRef.current = false
      setIsLoadingOlder(false)
    }
  }, [documentId, hasMoreOlderLogs, nextOlderPage])

  const handleLogsScroll = useCallback(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer || scrollContainer.scrollTop > OLDER_LOG_SCROLL_THRESHOLD_PX) return

    void loadOlderLogs()
  }, [loadOlderLogs])

  useEffect(() => {
    if (!documentId || isLoading || isError) return

    async function pollAgentLogs() {
      if (isPollingRef.current) return

      isPollingRef.current = true
      try {
        const response = await fetchAgentLogs(
          latestCreatedAtRef.current
            ? { documentId, after: latestCreatedAtRef.current }
            : { documentId, page: 1 }
        )
        pendingScrollToBottomRef.current = isNearBottom()

        setLogs((currentLogs) => mergeAgentLogs(currentLogs, response.results))
        if (response.results.length > 0) {
          latestCreatedAtRef.current = response.results.at(-1)?.created_at ?? latestCreatedAtRef.current
        }
        setHasPollingError(false)
      } catch {
        setHasPollingError(true)
      } finally {
        isPollingRef.current = false
      }
    }

    const intervalId = window.setInterval(() => {
      void pollAgentLogs()
    }, AGENT_LOG_POLLING_INTERVAL_MS)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [documentId, isError, isLoading, isNearBottom])

  return (
    <div className="flex h-full flex-col overflow-hidden bg-card" role="tabpanel" id="tabpanel-agent">
      <div className="min-h-0 flex-1 overflow-hidden">
        {isLoading && <AgentLogsLoadingState />}
        {!isLoading && isError && <AgentLogsErrorState />}
        {!isLoading && !isError && logs.length === 0 && <AgentLogsEmptyState />}
        {!isLoading && !isError && logs.length > 0 && (
          <div
            ref={scrollContainerRef}
            className="h-full overflow-y-auto p-4"
            aria-label="Agent log timeline"
            onScroll={handleLogsScroll}
          >
            {isLoadingOlder && (
              <div className="mb-3 rounded-md border border-border bg-muted/30 px-3 py-2 text-center text-xs text-muted-foreground">
                Loading older logs...
              </div>
            )}
            {hasPollingError && (
              <div className="mb-3 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-600">
                Live updates are temporarily unavailable. Retrying...
              </div>
            )}
            <ol className="relative space-y-3 before:absolute before:bottom-0 before:left-[13px] before:top-0 before:w-px before:bg-border">
              {logs.map((log) => (
                <AgentLogEntry key={log.id} log={log} />
              ))}
            </ol>
          </div>
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
        registerPromptContextInserter={chatContext.registerPromptContextInserter}
        onAddWholeDocument={chatContext.onAddWholeDocument}
        onAddCurrentPage={chatContext.onAddCurrentPage}
        isProcessing={isRunningInference}
        setIsRunningInference={setIsRunningInference}
        workflowSelection={workflowSelection}
        onTriggerSuccess={onTriggerSuccess}
      />
    </div>
  )
}
