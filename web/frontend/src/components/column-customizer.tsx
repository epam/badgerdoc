import { Settings2, GripVertical, RotateCcw, Eye, EyeOff } from 'lucide-react'
import { cn } from '@/helpers/utils'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { type TableColumn } from '@/shared/hooks/use-table-preferences'

interface ColumnCustomizerProps {
  columns: TableColumn[]
  visibleColumns: TableColumn[]
  isColumnVisible: (columnId: string) => boolean
  toggleColumn: (columnId: string) => void
  resetToDefaults: () => void
  className?: string
}

export function ColumnCustomizer({
  columns,
  isColumnVisible,
  toggleColumn,
  resetToDefaults,
  className,
}: ColumnCustomizerProps) {
  // Filter out columns that shouldn't be toggleable (like select and actions)
  const toggleableColumns = columns.filter((col) => col.id !== 'select' && col.id !== 'actions')

  const visibleCount = toggleableColumns.filter((col) => isColumnVisible(col.id)).length
  const totalCount = toggleableColumns.length

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className={cn('h-9 gap-2', className)}>
          <Settings2 className="h-4 w-4" />
          <span className="hidden sm:inline">Columns</span>
          <span className="text-xs text-muted-foreground tabular-nums">
            ({visibleCount}/{totalCount})
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Table Columns</h4>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-muted-foreground"
              onClick={resetToDefaults}
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
          </div>

          <Separator />

          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {toggleableColumns.map((column) => {
              const visible = isColumnVisible(column.id)

              return (
                <div
                  key={column.id}
                  className={cn(
                    'flex items-center gap-3 px-2 py-1.5 rounded-md transition-colors',
                    visible ? 'bg-muted/50' : 'opacity-60'
                  )}
                >
                  <GripVertical className="h-4 w-4 text-muted-foreground/50 cursor-grab" />

                  <div className="flex-1 flex items-center gap-2">
                    {visible ? (
                      <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                    ) : (
                      <EyeOff className="h-3.5 w-3.5 text-muted-foreground/50" />
                    )}
                    <span className={cn('text-sm', !visible && 'text-muted-foreground')}>
                      {column.label}
                    </span>
                  </div>

                  <Switch
                    checked={visible}
                    onCheckedChange={() => toggleColumn(column.id)}
                    className="scale-90"
                  />
                </div>
              )
            })}
          </div>

          <Separator />

          <p className="text-xs text-muted-foreground">
            Toggle columns on/off. Drag to reorder (coming soon).
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
