import type { ComponentProps, ReactNode } from 'react'
import { AlertCircle, ExternalLink, FileText } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/helpers/utils'
import { useWorkspaceDocument } from '@/shared/api/hooks/use-document-workspace'
import type { AgentLog, AgentLogLevel } from '@/shared/api/badgerdoc/types'
import {
  findPromptContextLinks,
  getPromptContextTokenLabel,
  parsePromptContextPath,
} from '@/features/workspace/helpers/extraction-chat-context'
import {
  formatLogTime,
  getWorkflowHeaderLabel,
  hasMeaningfulWorkflowParams,
  safeStringify,
  shouldShowSourceDocumentLink,
} from '@/features/workspace/helpers/agent-log-entry'
import { AGENT_TAB_ID } from './workspace-tabs'

interface AgentLogEntryProps {
  log: AgentLog
  currentDocumentId?: number | string
}

function getLevelVariant(level: AgentLogLevel): ComponentProps<typeof Badge>['variant'] {
  if (level === 'ERROR' || level === 'CRITICAL') {
    return 'destructive'
  }

  if (level === 'WARNING') {
    return 'warning'
  }

  if (level === 'DEBUG') {
    return 'outline'
  }

  return 'info'
}

function getEntryClassName(level: AgentLogLevel) {
  return cn(
    'rounded-md border border-border/70 bg-background p-3',
    level === 'DEBUG' && 'bg-muted/30 text-muted-foreground',
    level === 'WARNING' && 'border-amber-500/30 bg-amber-500/5',
    level === 'ERROR' && 'border-destructive/30 bg-destructive/5',
    level === 'CRITICAL' && 'border-destructive/50 bg-destructive/10 ring-1 ring-destructive/20'
  )
}

function getMarkerClassName(level: AgentLogLevel) {
  return cn(
    'absolute left-[7px] top-2 h-3 w-3 rounded-full border-2 border-card bg-muted ring-2 ring-border',
    level === 'INFO' && 'bg-sky-500 ring-sky-500/25',
    level === 'WARNING' && 'bg-amber-500 ring-amber-500/30',
    (level === 'ERROR' || level === 'CRITICAL') && 'bg-destructive ring-destructive/30'
  )
}

function MessageRenderer({ message }: { message: string }) {
  return <p className="whitespace-pre-wrap break-words text-sm">{message}</p>
}

function renderMarkdownInline(text: string) {
  const nodes: ReactNode[] = []
  const pattern = /(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^)\s]+)\))/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text))) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index))
    }

    const key = `${match.index}-${match[0]}`
    if (match[2]) {
      nodes.push(
        <strong key={key} className="font-semibold">
          {match[2]}
        </strong>
      )
    } else if (match[3]) {
      nodes.push(
        <code key={key} className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
          {match[3]}
        </code>
      )
    } else if (match[4] && match[5]) {
      nodes.push(
        <a
          key={key}
          href={match[5]}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-primary underline underline-offset-2"
        >
          {match[4]}
        </a>
      )
    }

    lastIndex = pattern.lastIndex
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex))
  }

  return nodes.length ? nodes : text
}

function MarkdownRenderer({ markdown }: { markdown: string }) {
  const blocks = markdown.split(/\n{2,}/)

  return (
    <div className="space-y-2 text-sm">
      {blocks.map((block, blockIndex) => {
        const trimmedBlock = block.trim()
        if (!trimmedBlock) return null

        return (
          <p key={`${blockIndex}-${trimmedBlock.slice(0, 12)}`} className="whitespace-pre-wrap">
            {renderMarkdownInline(trimmedBlock)}
          </p>
        )
      })}
    </div>
  )
}

function CodeRenderer({ code }: { code: string }) {
  return (
    <pre className="overflow-x-auto rounded-md border border-border bg-muted/40 p-3 text-xs">
      <code>{code}</code>
    </pre>
  )
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isScalarValue(value: unknown) {
  return ['string', 'number', 'boolean'].includes(typeof value)
}

function formatWorkflowParamText(value: unknown) {
  return typeof value === 'string' ? value : safeStringify(value)
}

function ReadOnlyPromptContextChip({ path }: { path: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="mx-0.5 inline-flex h-6 max-w-full select-none items-center rounded border border-blue-200 bg-blue-50 px-1.5 text-xs font-medium text-blue-700 align-baseline">
          <span className="truncate">{getPromptContextTokenLabel(path)}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">{path}</TooltipContent>
    </Tooltip>
  )
}

function renderPromptTextWithContextChips(text: string) {
  const nodes: ReactNode[] = []
  let cursor = 0

  findPromptContextLinks(text).forEach(({ raw, path, index }) => {
    const token = parsePromptContextPath(path)

    if (index > cursor) {
      nodes.push(text.slice(cursor, index))
    }

    if (token) {
      nodes.push(<ReadOnlyPromptContextChip key={`${index}-${path}`} path={path} />)
    } else {
      nodes.push(raw)
    }

    cursor = index + raw.length
  })

  if (cursor < text.length) {
    nodes.push(text.slice(cursor))
  }

  return nodes.length ? nodes : text
}

function WorkflowPromptRenderer({ value }: { value: unknown }) {
  const text = formatWorkflowParamText(value)

  return (
    <div className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-sm">
      {renderPromptTextWithContextChips(text)}
    </div>
  )
}

function WorkflowScalarRenderer({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="flex min-w-0 gap-2 rounded-md border border-border/70 bg-muted/20 px-3 py-2 text-sm">
      <span className="shrink-0 font-medium text-muted-foreground">{label}:</span>
      <span className="min-w-0 break-words">{formatWorkflowParamText(value)}</span>
    </div>
  )
}

function WorkflowComplexRenderer({ label, value }: { label: string; value: unknown }) {
  return (
    <details className="rounded-md border border-border bg-muted/20">
      <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-muted-foreground">
        {label}
      </summary>
      <pre className="max-h-72 overflow-auto border-t border-border bg-muted/40 p-3 text-xs">
        <code>{safeStringify(value)}</code>
      </pre>
    </details>
  )
}

function WorkflowParamFieldRenderer({ label, value }: { label: string; value: unknown }) {
  if (isScalarValue(value)) {
    return <WorkflowScalarRenderer label={label} value={value} />
  }

  return <WorkflowComplexRenderer label={label} value={value} />
}

function WorkflowParamsRenderer({ value }: { value: unknown }) {
  if (!isRecord(value)) {
    return (
      <PayloadSection label="Workflow details">
        <WorkflowScalarRenderer label="value" value={value} />
      </PayloadSection>
    )
  }

  const userInput = value.llm_params
  const hasUserInput = hasMeaningfulWorkflowParams(userInput)
  const detailEntries = Object.entries(value).filter(
    ([key, entryValue]) => key !== 'llm_params' && hasMeaningfulWorkflowParams(entryValue)
  )

  if (!hasUserInput && detailEntries.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      {hasUserInput && <WorkflowPromptRenderer value={userInput} />}
      {detailEntries.length > 0 && (
        <PayloadSection label="Workflow details">
          <div className="space-y-2">
            {detailEntries.map(([key, entryValue]) => (
              <WorkflowParamFieldRenderer key={key} label={key} value={entryValue} />
            ))}
          </div>
        </PayloadSection>
      )}
    </div>
  )
}

function SourceDocumentLink({ documentId }: { documentId: number | string }) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      className="text-xs font-medium text-primary underline underline-offset-2 hover:text-primary/80 focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none"
      onClick={() => {
        void navigate({
          to: '/documents/$id',
          params: { id: String(documentId) },
          search: { tag: AGENT_TAB_ID },
        })
      }}
    >
      Document #{documentId}
    </button>
  )
}

function DocumentPayloadRenderer({ documentId }: { documentId: number | string }) {
  const navigate = useNavigate()
  const { data: document, isLoading, isError } = useWorkspaceDocument(String(documentId))

  if (isLoading) {
    return <Skeleton className="h-16 w-full" />
  }

  const title = document?.title || `Document ${documentId}`

  return (
    <button
      type="button"
      className={cn(
        'flex w-full min-w-0 items-center gap-3 rounded-md border border-border bg-muted/20 p-3 text-left transition-colors',
        'hover:border-border/80 hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none'
      )}
      onClick={() => {
        void navigate({
          to: '/documents/$id',
          params: { id: String(documentId) },
          search: { tag: AGENT_TAB_ID },
        })
      }}
    >
      {document?.thumbnailUrl ? (
        <img
          src={document.thumbnailUrl}
          alt=""
          className="h-12 w-10 shrink-0 rounded-sm border border-border object-cover"
        />
      ) : (
        <span className="flex h-12 w-10 shrink-0 items-center justify-center rounded-sm border border-border bg-background">
          <FileText className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{title}</span>
        <span className="mt-0.5 block text-xs text-muted-foreground">
          {isError ? 'Document details unavailable' : `Document ${documentId}`}
        </span>
      </span>
      <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </button>
  )
}

function PayloadSection({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      {children}
    </div>
  )
}

function AgentLogPayloadRenderer({ log }: { log: AgentLog }) {
  const payload = log.log
  const hasMessage = 'message' in payload
  const hasMarkdown = 'markdown' in payload
  const hasCode = 'code' in payload
  const hasDocument = payload.document !== undefined && payload.document !== null
  const hasWorkflowParams = hasMeaningfulWorkflowParams(payload.workflow_params)
  const hasPayload = hasMessage || hasMarkdown || hasCode || hasDocument || hasWorkflowParams

  if (!hasPayload) {
    return <p className="text-sm text-muted-foreground">No payload details.</p>
  }

  return (
    <div className="space-y-3">
      {hasMessage && (
        <PayloadSection label="Message">
          <MessageRenderer message={payload.message ?? ''} />
        </PayloadSection>
      )}
      {hasMarkdown && (
        <PayloadSection label="Markdown">
          <MarkdownRenderer markdown={payload.markdown ?? ''} />
        </PayloadSection>
      )}
      {hasCode && (
        <PayloadSection label="Code">
          <CodeRenderer code={payload.code ?? ''} />
        </PayloadSection>
      )}
      {hasDocument && (
        <PayloadSection label="Document">
          <DocumentPayloadRenderer documentId={payload.document as number | string} />
        </PayloadSection>
      )}
      {hasWorkflowParams && (
        <WorkflowParamsRenderer value={payload.workflow_params} />
      )}
    </div>
  )
}

export function AgentLogEntry({ log, currentDocumentId }: AgentLogEntryProps) {
  const workflowHeaderLabel = getWorkflowHeaderLabel(log.log.workflow_params)
  const shouldShowSourceDocument = shouldShowSourceDocumentLink({
    currentDocumentId,
    sourceDocumentId: log.document,
  })

  return (
    <li className="relative pl-8">
      <span aria-hidden="true" className={getMarkerClassName(log.level)} />
      <article className={getEntryClassName(log.level)}>
        <div className="mb-3 flex min-w-0 flex-wrap items-center gap-2">
          <Badge variant={getLevelVariant(log.level)}>{log.level}</Badge>
          {log.source && (
            <span className="text-xs font-medium text-muted-foreground">{log.source}</span>
          )}
          {workflowHeaderLabel && (
            <span className="text-xs font-medium text-muted-foreground">
              {workflowHeaderLabel}
            </span>
          )}
          {log.task && <span className="text-xs text-muted-foreground">Task {log.task}</span>}
          <time className="text-xs text-muted-foreground" dateTime={log.created_at}>
            {formatLogTime(log.created_at)}
          </time>
          {shouldShowSourceDocument && <SourceDocumentLink documentId={log.document} />}
          {log.level === 'CRITICAL' && (
            <AlertCircle className="h-4 w-4 text-destructive" aria-hidden="true" />
          )}
        </div>
        <AgentLogPayloadRenderer log={log} />
      </article>
    </li>
  )
}
