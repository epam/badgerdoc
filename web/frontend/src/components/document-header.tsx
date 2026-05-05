import { Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn, getStatusColor } from '@/helpers/utils'
import { useNavigationHistory } from '@/shared/hooks/use-navigation-history'
import type { ReactNode } from 'react'

interface DocumentHeaderProps {
  documentId: string
  title: string
  authors?: string[]
  date?: string
  /** Current task/document status name (e.g., "Not Processed", "Relevance Check") */
  statusName?: string
  backLink?: string
  backSearch?: Record<string, unknown>
  backLabel?: string
  useSmartBack?: boolean
  className?: string
  children?: ReactNode
}

export function DocumentHeader({
  documentId: _documentId,
  title,
  authors,
  date: _date,
  statusName,
  backLink = '/tasks',
  backSearch,
  backLabel = 'Back',
  useSmartBack = true,
  className,
  children,
}: DocumentHeaderProps) {
  const statusColors = statusName ? getStatusColor(statusName) : null
  const { goBack } = useNavigationHistory({ fallbackPath: backLink, fallbackSearch: backSearch })

  return (
    <div className={cn('border-b border-border/40 bg-card', className)}>
      <div className="px-4 py-2 lg:px-6">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              {useSmartBack ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={goBack}
                  className="h-8 gap-1 px-2 text-muted-foreground"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {backLabel}
                </Button>
              ) : (
                <Link to={backLink} search={backSearch}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 gap-1 px-2 text-muted-foreground"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    {backLabel}
                  </Button>
                </Link>
              )}
              <span className="text-border">|</span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <h1 className="truncate text-foreground text-sm font-medium cursor-default">
                    {title}
                  </h1>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-md">
                  <p className="text-sm">{title}</p>
                </TooltipContent>
              </Tooltip>
              <span className="ml-2 shrink-0 text-sm text-muted-foreground hidden lg:inline-flex items-center gap-2">
                {authors && authors.length > 0 && (
                  <>
                    <span className="text-border">·</span>
                    <span>
                      {authors[0]}
                      {authors.length > 1 ? ` +${authors.length - 1}` : ''}
                    </span>
                  </>
                )}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {statusName && statusColors && (
              <span
                className={cn(
                  'rounded-full px-2.5 py-0.5 text-xs font-medium',
                  statusColors.bg,
                  statusColors.text
                )}
              >
                {statusName}
              </span>
            )}

            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
