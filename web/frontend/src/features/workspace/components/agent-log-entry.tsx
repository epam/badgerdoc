import type { ComponentProps, ReactNode } from 'react'
import { AlertCircle, ExternalLink, FileText } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/helpers/utils'
import { useWorkspaceDocument } from '@/shared/api/hooks/use-document-workspace'
import type { AgentLog, AgentLogLevel } from '@/shared/api/badgerdoc/types'
import {
  formatLogTime,
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

function WorkflowParamsRenderer({ value }: { value: unknown }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-md border border-border bg-muted/40 p-3 text-xs">
      <code>{safeStringify(value)}</code>
    </pre>
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
        <PayloadSection label="Workflow Params">
          <WorkflowParamsRenderer value={payload.workflow_params} />
        </PayloadSection>
      )}
    </div>
  )
}

export function AgentLogEntry({ log, currentDocumentId }: AgentLogEntryProps) {
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
