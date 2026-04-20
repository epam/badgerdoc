import { useMemo, useRef, useCallback, type KeyboardEvent } from 'react'
import { Check, Circle } from 'lucide-react'
import { cn } from '@/helpers/utils.ts'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip.tsx'
import { Tag } from '@/shared/api/badgerdoc/types.ts'

type TabStatus = 'idle' | 'in_progress' | 'complete' | 'locked'

interface WorkspaceTabsProps {
  activeTab: string
  onTabChange: (tab: Tag['tag']) => void
  /** Available extraction tags from the API */
  extractionTags?: Tag[]
  /** Whether extraction tags are still loading */
  isLoadingTags?: boolean
  /** Current task status ID - used to determine which tabs are locked */
  currentStatusId?: number
  /** Current task status name - used as fallback for tab locking */
  currentStatusName?: string
  tabStatus?: Partial<Record<string, TabStatus>>
}

interface TabConfig {
  id: string
  label: string
  shortcut: string
  order: number
}

function TabStatusIndicator({ status }: { status: TabStatus }) {
  if (status === 'complete') {
    return <Check className="h-3 w-3 text-mint" />
  }
  if (status === 'in_progress') {
    return <Circle className="h-2 w-2 fill-amber-500 text-amber-500" />
  }
  return null
}

/**
 * Determine if a tab should be locked based on current status.
 * For now, tabs are unlocked - implement workflow logic as needed.
 */
function getTabLockInfo(
  _tabId: string,
  _currentStatusId?: number,
  _currentStatusName?: string
): { isLocked: boolean; reason?: string } {
  // TODO: Implement tab locking logic based on workflow status
  // For now, all tabs are unlocked
  return { isLocked: false }
}

export function WorkspaceTabs({
  activeTab,
  onTabChange,
  extractionTags = [],
  isLoadingTags = false,
  currentStatusId,
  currentStatusName,
  tabStatus = {},
}: WorkspaceTabsProps) {
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])

  // Build tabs from extraction tags + hardcoded overview
  const allTabs: TabConfig[] = useMemo(() => {
    const tabs: TabConfig[] = [{ id: 'overview', label: 'Overview', shortcut: '1', order: 0 }]

    // Add dynamic tabs from extraction tags
    extractionTags.forEach((tag, index) => {
      tabs.push({
        id: tag.tag,
        label: tag.literal,
        order: tag.order,
        shortcut: String(index + 2),
      })
    })

    return tabs.sort((a, b) => (a.order || 0) - (b.order || 0))
  }, [extractionTags])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent, currentIndex: number) => {
      let newIndex = currentIndex

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          newIndex = currentIndex === 0 ? allTabs.length - 1 : currentIndex - 1
          break
        case 'ArrowRight':
          e.preventDefault()
          newIndex = currentIndex === allTabs.length - 1 ? 0 : currentIndex + 1
          break
        case 'Home':
          e.preventDefault()
          newIndex = 0
          break
        case 'End':
          e.preventDefault()
          newIndex = allTabs.length - 1
          break
        default:
          return
      }

      const { isLocked } = getTabLockInfo(allTabs[newIndex].id, currentStatusId, currentStatusName)
      if (!isLocked) {
        tabRefs.current[newIndex]?.focus()
        onTabChange(allTabs[newIndex].id)
      }
    },
    [allTabs, onTabChange, currentStatusId, currentStatusName]
  )

  // Show skeleton tabs while loading
  if (isLoadingTags) {
    return (
      <div className="flex items-center border-b border-border/40 bg-card px-4">
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="h-4 w-20 animate-pulse rounded bg-muted" />
        </div>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        </div>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="h-4 w-28 animate-pulse rounded bg-muted" />
        </div>
      </div>
    )
  }

  return (
    <div
      className="flex items-center border-b border-border/40 bg-card px-4"
      role="tablist"
      aria-label="Document workspace tabs"
    >
      {allTabs.map((tab, index) => {
        const isActive = activeTab === tab.id
        const { isLocked, reason } = getTabLockInfo(tab.id, currentStatusId, currentStatusName)
        const status = isLocked ? 'locked' : tabStatus[tab.id] || 'idle'

        const button = (
          <button
            key={tab.id}
            ref={(el) => {
              tabRefs.current[index] = el
            }}
            role="tab"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            aria-disabled={isLocked}
            tabIndex={isActive ? 0 : -1}
            onClick={() => !isLocked && onTabChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={cn(
              'flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors -mb-px',
              isLocked
                ? 'border-transparent text-muted-foreground/50 cursor-not-allowed'
                : isActive
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <span className={cn(isLocked && 'opacity-50')}>{tab.label}</span>
            <TabStatusIndicator status={status} />
          </button>
        )

        if (isLocked && reason) {
          return (
            <Tooltip key={tab.id}>
              <TooltipTrigger asChild>{button}</TooltipTrigger>
              <TooltipContent>
                <p>{reason}</p>
              </TooltipContent>
            </Tooltip>
          )
        }

        return button
      })}
    </div>
  )
}
