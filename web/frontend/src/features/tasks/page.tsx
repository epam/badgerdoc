import { useState, useMemo, useCallback, ChangeEvent, MouseEvent } from 'react'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { Search, X, Filter, Bookmark, BookmarkPlus, Trash2, ChevronDown, Star } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { DateRangePicker, type DateRange } from '@/components/date-range-picker'
import { ColumnCustomizer } from '@/components/column-customizer'
import { cn, getStatusColor, formatTimeAgo } from '@/helpers/utils'
import { useSavedFilters, type SavedFilter } from '@/shared/hooks/use-saved-filters'
import { useTablePreferences, type TableColumn } from '@/shared/hooks/use-table-preferences'
import { useTaskStatuses } from '@/shared/api/hooks'
import { useFilteredTasks, SearchDocument } from '@/shared/api/hooks/use-tasks'
import {
  DEFAULT_TASK_FILTERS,
  TaskFilters,
  taskFiltersFromSearch,
  TaskFiltersSearch,
  taskFiltersToSearch,
} from '@/helpers/task-filters-search'

// Define available columns for document list
const documentListColumns: TableColumn[] = [
  { id: 'title', label: 'Title', defaultVisible: true },
  { id: 'type', label: 'Type', defaultVisible: true },
  { id: 'authors', label: 'Authors', defaultVisible: true },
  { id: 'date', label: 'Date', defaultVisible: true },
  { id: 'status', label: 'Status', defaultVisible: true },
  { id: 'action', label: 'Action', defaultVisible: true },
]

// Default status tabs - will be replaced with dynamic data from API
const defaultStatusTabs = [{ id: 'all', label: 'All' }]

interface DocumentRowProps {
  doc: SearchDocument
  isColumnVisible: (columnId: string) => boolean
  filtersSearch: TaskFiltersSearch
}

function DocumentRow({ doc, isColumnVisible, filtersSearch }: DocumentRowProps) {
  const status = getStatusColor(doc.status)

  return (
    <Link
      to="/tasks/$taskId"
      params={{ taskId: String(doc.taskId) }}
      search={filtersSearch}
      className={cn('group flex items-center gap-4 px-4 py-4 transition-colors hover:bg-muted/50')}
    >
      <div className="min-w-0 flex-1">
        {isColumnVisible('title') && (
          <div className="flex items-center gap-2">
            <span className="truncate font-medium text-foreground">{doc.title}</span>
            {doc.priority === 'high' && (
              <span className="text-xs font-medium text-primary">Priority</span>
            )}
          </div>
        )}
        {isColumnVisible('title') && doc.filename && doc.filename !== doc.title && (
          <div className="mt-0.5 text-xs text-muted-foreground/70 truncate">{doc.filename}</div>
        )}

        <div className="mt-1 flex items-center text-sm text-muted-foreground [&>span:not(:last-child)]:after:content-['·'] [&>span:not(:last-child)]:after:mx-2">
          {isColumnVisible('type') && <span className="capitalize">{doc.type}</span>}
          {isColumnVisible('authors') && doc.authors?.length > 0 && (
            <span>
              {doc.authors.slice(0, 2).join(', ')}
              {doc.authors.length > 2 ? ` +${doc.authors.length - 2}` : ''}
            </span>
          )}
          {isColumnVisible('date') && <span>{formatTimeAgo(doc.createdAt)}</span>}
        </div>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        {isColumnVisible('status') && (
          <span
            className={cn(
              'hidden rounded-full px-2.5 py-0.5 text-xs font-medium sm:inline-block',
              status.bg,
              status.text
            )}
          >
            {doc.statusName}
          </span>
        )}
        {isColumnVisible('action') && (
          <span className="text-sm font-medium text-primary">{doc.actionLabel} →</span>
        )}
      </div>
    </Link>
  )
}

interface EmptyStateProps {
  status: string
  query: string
  statusTabs: { id: string; label: string }[]
}

function EmptyState({ status, query, statusTabs }: EmptyStateProps) {
  const statusLabel = statusTabs.find((t) => t.id === status)?.label || 'All'

  return (
    <div className="py-16 text-center">
      <h3 className="text-lg font-semibold text-foreground">
        {query ? 'No results found' : 'All caught up!'}
      </h3>
      <p className="mt-2 text-muted-foreground">
        {query
          ? `No documents match "${query}" in ${statusLabel.toLowerCase()}.`
          : `There are no documents in ${statusLabel.toLowerCase()} right now.`}
      </p>
    </div>
  )
}

function SearchSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div>
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-5 w-80 mt-1" />
      </div>

      {/* Tabs skeleton */}
      <div className="flex items-center gap-1 border-b border-border pb-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-9 w-20" />
        ))}
      </div>

      {/* Filters skeleton */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <Skeleton className="h-10 flex-1 rounded-xl" />
        <div className="flex gap-2">
          <Skeleton className="h-10 w-[120px] rounded-xl" />
          <Skeleton className="h-10 w-[150px] rounded-xl" />
        </div>
      </div>

      {/* Results summary skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
      </div>

      {/* Results list skeleton */}
      <div className="divide-y divide-border rounded-xl border border-border">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center justify-between gap-4 px-4 py-4">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-5 w-3/4" />
              <div className="mt-2 flex items-center gap-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-20" />
              </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface TasksPageProps {
  title?: string
  description?: string
}

export function TasksPage({
  title = 'Documents Review',
  description = 'Browse and manage documents in the processing pipeline',
}: TasksPageProps) {
  const navigate = useNavigate()
  const search = useSearch({ from: '/tasks' }) as TaskFiltersSearch
  const filters = useMemo(() => taskFiltersFromSearch(search), [search])
  const { query, activeTab, sortBy, typeFilter, dateTo, dateFrom } = filters
  const filtersSearch = useMemo(() => taskFiltersToSearch(filters), [filters])

  // Saved filters
  const { savedFilters, addFilter, removeFilter, setDefault } = useSavedFilters()
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [newFilterName, setNewFilterName] = useState('')
  const [newFilterAsDefault, setNewFilterAsDefault] = useState(false)

  // Column preferences
  const columnPrefs = useTablePreferences('document-search', documentListColumns)

  const updateFilters = useCallback(
    (next: Partial<TaskFilters>, replace = false) => {
      const mergedFilters: TaskFilters = { ...filters, ...next }
      void navigate({
        to: '/tasks',
        search: taskFiltersToSearch(mergedFilters),
        replace,
      })
    },
    [filters, navigate]
  )

  const clearFilters = useCallback(() => {
    void navigate({ to: '/tasks', search: {}, replace: false })
  }, [navigate])

  const setQuery = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      updateFilters({ query: event.target.value }, true)
    },
    [updateFilters]
  )

  const setActiveTab = useCallback(
    (value: string) => {
      updateFilters({ activeTab: value })
    },
    [updateFilters]
  )

  const setSortBy = useCallback(
    (value: string) => {
      updateFilters({ sortBy: value as TaskFilters['sortBy'] })
    },
    [updateFilters]
  )

  const setTypeFilter = useCallback(
    (value: string) => {
      updateFilters({ typeFilter: value as TaskFilters['typeFilter'] })
    },
    [updateFilters]
  )

  const setDateRange = useCallback(
    ({ from, to }: DateRange) => {
      updateFilters({ dateFrom: from, dateTo: to })
    },
    [updateFilters]
  )

  const hasDateFilter = !!dateFrom || !!dateTo
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(hasDateFilter)

  const { data: filteredTasksData, isLoading } = useFilteredTasks(filters)
  const filteredDocuments = useMemo(
    () => filteredTasksData?.results ?? [],
    [filteredTasksData?.results]
  )

  // Fetch available statuses for dynamic tabs
  const { data: statusesData } = useTaskStatuses()

  // Build status tabs from API data
  const statusTabs = useMemo(() => {
    if (!statusesData) return defaultStatusTabs

    const tabs: { id: string; label: string }[] = [{ id: 'all', label: 'All' }]

    for (const status of statusesData) {
      tabs.push({
        id: status.name,
        label: status.name,
      })
    }
    return tabs
  }, [statusesData])

  const hasActiveFilters =
    query ||
    activeTab !== DEFAULT_TASK_FILTERS.activeTab ||
    typeFilter !== DEFAULT_TASK_FILTERS.typeFilter ||
    sortBy !== DEFAULT_TASK_FILTERS.sortBy ||
    hasDateFilter
  const advancedFilterCount = hasDateFilter ? 1 : 0

  const applyFilter = useCallback(
    (filter: SavedFilter) => {
      updateFilters({
        query: filter.filters.query,
        activeTab: filter.filters.activeTab,
        sortBy: filter.filters.sortBy as TaskFilters['sortBy'],
        typeFilter: filter.filters.typeFilter as TaskFilters['typeFilter'],
        dateFrom: filter.filters.dateFrom ? new Date(filter.filters.dateFrom) : null,
        dateTo: filter.filters.dateTo ? new Date(filter.filters.dateTo) : null,
      })

      if (filter.filters.dateFrom || filter.filters.dateTo) {
        setShowAdvancedFilters(true)
      }

      toast.success(`Applied filter: ${filter.name}`)
    },
    [updateFilters]
  )

  // Save current filters
  const handleSaveFilter = useCallback(() => {
    if (!newFilterName.trim()) {
      toast.error('Please enter a name for the filter')
      return
    }

    addFilter({
      name: newFilterName.trim(),
      isDefault: newFilterAsDefault,
      filters: {
        query,
        activeTab,
        sortBy,
        typeFilter,
        dateFrom: dateFrom?.toISOString() || null,
        dateTo: dateTo?.toISOString() || null,
      },
    })

    toast.success(`Saved filter: ${newFilterName}`)
    setSaveDialogOpen(false)
    setNewFilterName('')
    setNewFilterAsDefault(false)
  }, [
    newFilterName,
    newFilterAsDefault,
    query,
    activeTab,
    sortBy,
    typeFilter,
    addFilter,
    dateFrom,
    dateTo,
  ])

  const handleDeleteFilter = useCallback(
    (filter: SavedFilter, e: MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      removeFilter(filter.id)
      toast.success(`Deleted filter: ${filter.name}`)
    },
    [removeFilter]
  )

  const handleSetDefault = useCallback(
    (filter: SavedFilter, e: MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      setDefault(filter.id)
      toast.success(`Set "${filter.name}" as default filter`)
    },
    [setDefault]
  )

  if (isLoading) {
    return <SearchSkeleton />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-muted-foreground">{description}</p>
      </div>

      {/* Simple Tab Bar */}
      <div className="flex items-stretch gap-1 border-b border-border">
        {statusTabs.map((tab) => {
          const isActive = activeTab === tab.id

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-4 py-2.5 text-sm font-medium transition-all duration-150 border-b-2 -mb-px hover:cursor-pointer',
                isActive
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
              )}
            >
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Search and Filters - flat, no card wrapper */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by title or author..."
            value={query}
            onChange={setQuery}
            className="pl-10 h-10"
          />
        </div>

        <div className="flex gap-2">
          {/* Saved Filters Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="h-10 gap-2">
                <Bookmark className="h-4 w-4" />
                <span className="hidden sm:inline">Saved</span>
                <ChevronDown className="h-3 w-3 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              {savedFilters.length > 0 ? (
                <>
                  {savedFilters.map((filter) => (
                    <DropdownMenuItem
                      key={filter.id}
                      onClick={() => applyFilter(filter)}
                      className="group flex items-center justify-between py-2"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {filter.isDefault ? (
                          <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 flex-shrink-0" />
                        ) : (
                          <Bookmark className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                        )}
                        <span className="truncate">{filter.name}</span>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {!filter.isDefault && (
                          <button
                            onClick={(e) => handleSetDefault(filter, e)}
                            className="p-1 hover:bg-muted rounded"
                            title="Set as default"
                          >
                            <Star className="h-3 w-3" />
                          </button>
                        )}
                        {!filter.id.startsWith('preset-') && (
                          <button
                            onClick={(e) => handleDeleteFilter(filter, e)}
                            className="p-1 hover:bg-destructive/10 hover:text-destructive rounded"
                            title="Delete filter"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </DropdownMenuItem>
                  ))}
                  <DropdownMenuSeparator />
                </>
              ) : null}
              <DropdownMenuItem onClick={() => setSaveDialogOpen(true)} className="gap-2">
                <BookmarkPlus className="h-4 w-4" />
                Save current filter...
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[120px] h-10" aria-label="Filter by document type">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              <SelectItem value="patent">Patents</SelectItem>
              <SelectItem value="paper">Papers</SelectItem>
              <SelectItem value="article">Articles</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[150px] h-10" aria-label="Sort documents by">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest first</SelectItem>
              <SelectItem value="oldest">Oldest first</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant={showAdvancedFilters ? 'secondary' : 'outline'}
            size="icon"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="h-10 w-10 relative"
            aria-label={showAdvancedFilters ? 'Hide advanced filters' : 'Show advanced filters'}
            aria-expanded={showAdvancedFilters}
          >
            <Filter className="h-4 w-4" />
            {advancedFilterCount > 0 && (
              <span
                className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground"
                aria-label={`${advancedFilterCount} filters active`}
              >
                {advancedFilterCount}
              </span>
            )}
          </Button>

          <ColumnCustomizer
            columns={documentListColumns}
            visibleColumns={columnPrefs.visibleColumns}
            isColumnVisible={columnPrefs.isColumnVisible}
            toggleColumn={columnPrefs.toggleColumn}
            resetToDefaults={columnPrefs.resetToDefaults}
          />

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="icon"
              onClick={clearFilters}
              className="h-10 w-10"
              aria-label="Clear all filters"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Advanced Filters */}
      {showAdvancedFilters && (
        <div className="flex flex-wrap gap-3 rounded-xl border border-border bg-card p-4">
          <DateRangePicker
            value={{ from: dateFrom, to: dateTo }}
            onChange={setDateRange}
            placeholder="Created date"
            className="w-[200px]"
          />
        </div>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <p className="text-muted-foreground">
            {filteredDocuments.length} {filteredDocuments.length === 1 ? 'document' : 'documents'}
            {activeTab !== 'all' && ` in ${statusTabs.find((t) => t.id === activeTab)?.label}`}
          </p>
        </div>
        {hasActiveFilters && (
          <button onClick={clearFilters} className="font-medium text-primary hover:underline">
            Clear filters
          </button>
        )}
      </div>

      {/* Results - simple list */}
      {filteredDocuments.length > 0 ? (
        <div className="divide-y divide-border rounded-xl border border-border">
          {filteredDocuments.map((doc) => (
            <DocumentRow
              key={doc.id}
              doc={doc}
              isColumnVisible={columnPrefs.isColumnVisible}
              filtersSearch={filtersSearch}
            />
          ))}
        </div>
      ) : (
        <EmptyState status={activeTab} query={query} statusTabs={statusTabs} />
      )}

      {/* Save Filter Dialog */}
      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Save Current Filter</DialogTitle>
            <DialogDescription>
              Save your current filter settings for quick access later.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="filter-name" className="text-sm font-medium">
                Filter name
              </label>
              <Input
                id="filter-name"
                placeholder="e.g., My review queue"
                value={newFilterName}
                onChange={(e) => setNewFilterName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSaveFilter()}
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="set-default"
                checked={newFilterAsDefault}
                onCheckedChange={(checked) => setNewFilterAsDefault(checked === true)}
              />
              <label htmlFor="set-default" className="text-sm text-muted-foreground">
                Set as default filter
              </label>
            </div>
            <div className="rounded-lg bg-muted p-3 text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Current settings:</p>
              <ul className="space-y-0.5 text-xs">
                {activeTab !== 'all' && (
                  <li>Status: {statusTabs.find((t) => t.id === activeTab)?.label}</li>
                )}
                {typeFilter !== 'all' && <li>Type: {typeFilter}</li>}
                {sortBy !== 'newest' && <li>Sort: {sortBy.replace('_', ' ')}</li>}
                {query && <li>Search: "{query}"</li>}
                {!hasActiveFilters && <li>No filters applied</li>}
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveFilter} disabled={!newFilterName.trim()}>
              <BookmarkPlus className="h-4 w-4 mr-2" />
              Save Filter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
