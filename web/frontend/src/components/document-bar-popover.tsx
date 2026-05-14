import {
  useState,
  type ComponentProps,
  type ComponentPropsWithoutRef,
  type ReactElement,
  type ReactNode,
} from 'react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/helpers/utils'

type PopoverContentProps = ComponentPropsWithoutRef<typeof PopoverContent>

interface DocumentBarPopoverProps extends Pick<
  PopoverContentProps,
  | 'align'
  | 'side'
  | 'sideOffset'
  | 'onInteractOutside'
  | 'onEscapeKeyDown'
  | 'onOpenAutoFocus'
  | 'onCloseAutoFocus'
> {
  children: ReactNode
  contentClassName?: string
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
  title?: ReactNode
  trigger: (state: { isOpen: boolean }) => ReactElement
}

interface DocumentBarPopoverButtonProps extends Omit<
  ComponentProps<typeof Button>,
  'size' | 'variant'
> {
  isOpen: boolean
}

export function DocumentBarPopover({
  children,
  contentClassName,
  defaultOpen = false,
  open,
  onOpenChange,
  title,
  trigger,
  align = 'start',
  sideOffset,
  ...contentProps
}: DocumentBarPopoverProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen

  const handleOpenChange = (nextOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(nextOpen)
    }

    onOpenChange?.(nextOpen)
  }

  return (
    <Popover open={isOpen} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>{trigger({ isOpen })}</PopoverTrigger>
      <PopoverContent
        align={align}
        sideOffset={sideOffset}
        className={cn('max-w-[calc(100vw-2rem)] rounded-xl', contentClassName)}
        {...contentProps}
      >
        {title ? (
          <div className="border-b border-border/40 px-4 py-3">
            <h2 className="font-semibold">{title}</h2>
          </div>
        ) : null}
        {children}
      </PopoverContent>
    </Popover>
  )
}

export function DocumentBarPopoverButton({
  children,
  className,
  isOpen,
  ...props
}: DocumentBarPopoverButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={cn(
        'h-9 justify-start gap-2 rounded-xl border-border/70 bg-background px-3 text-foreground shadow-sm hover:bg-muted/60',
        isOpen && 'border-primary/50 bg-muted/70 text-foreground',
        className
      )}
      aria-expanded={isOpen}
      {...props}
    >
      {children}
    </Button>
  )
}
