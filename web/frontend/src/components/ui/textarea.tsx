import * as React from 'react'

import { cn } from '@/helpers/utils'

function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'border-border placeholder:text-muted-foreground focus-visible:border-primary focus-visible:ring-primary/20 flex field-sizing-content min-h-16 w-full rounded-xl border bg-background px-3 py-2 text-sm transition-colors outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50 hover:border-muted-foreground/50',
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
