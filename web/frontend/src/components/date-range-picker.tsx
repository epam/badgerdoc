import { useState, type MouseEvent } from 'react'
import { Calendar, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/helpers/utils'

export interface DateRange {
  from: Date | null
  to: Date | null
}

interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
  placeholder?: string
  className?: string
}

const presets = [
  { label: 'Today', getValue: () => ({ from: new Date(), to: new Date() }) },
  {
    label: 'Yesterday',
    getValue: () => {
      const date = new Date()
      date.setDate(date.getDate() - 1)
      return { from: date, to: date }
    },
  },
  {
    label: 'Last 7 days',
    getValue: () => {
      const to = new Date()
      const from = new Date()
      from.setDate(from.getDate() - 7)
      return { from, to }
    },
  },
  {
    label: 'Last 30 days',
    getValue: () => {
      const to = new Date()
      const from = new Date()
      from.setDate(from.getDate() - 30)
      return { from, to }
    },
  },
  {
    label: 'This month',
    getValue: () => {
      const to = new Date()
      const from = new Date(to.getFullYear(), to.getMonth(), 1)
      return { from, to }
    },
  },
]

function formatDate(date: Date | null): string {
  if (!date) return ''
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined,
  })
}

export function DateRangePicker({
  value,
  onChange,
  placeholder = 'Select date range',
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false)

  const hasValue = value.from || value.to
  const displayValue = hasValue
    ? value.from && value.to
      ? `${formatDate(value.from)} - ${formatDate(value.to)}`
      : value.from
        ? `From ${formatDate(value.from)}`
        : `To ${formatDate(value.to)}`
    : placeholder

  const handlePresetClick = (preset: (typeof presets)[0]) => {
    onChange(preset.getValue())
    setOpen(false)
  }

  const handleClear = (e: MouseEvent) => {
    e.stopPropagation()
    onChange({ from: null, to: null })
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'h-10 justify-start text-left font-normal',
            !hasValue && 'text-muted-foreground',
            className
          )}
        >
          <Calendar className="mr-2 h-4 w-4" />
          <span className="flex-1 truncate">{displayValue}</span>
          {hasValue && (
            <X
              className="ml-2 h-3.5 w-3.5 shrink-0 text-muted-foreground hover:text-foreground"
              onClick={handleClear}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="p-3">
          <div className="mb-2 text-sm font-medium text-muted-foreground">Quick select</div>
          <div className="flex flex-col gap-1">
            {presets.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePresetClick(preset)}
                className="rounded-lg px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
        <div className="border-t border-border p-3">
          <div className="mb-2 text-sm font-medium text-muted-foreground">Custom range</div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="mb-1 block text-xs text-muted-foreground">From</label>
              <input
                type="date"
                value={value.from?.toISOString().split('T')[0] || ''}
                onChange={(e) =>
                  onChange({
                    ...value,
                    from: e.target.value ? new Date(e.target.value) : null,
                  })
                }
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-xs text-muted-foreground">To</label>
              <input
                type="date"
                value={value.to?.toISOString().split('T')[0] || ''}
                onChange={(e) =>
                  onChange({
                    ...value,
                    to: e.target.value ? new Date(e.target.value) : null,
                  })
                }
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
