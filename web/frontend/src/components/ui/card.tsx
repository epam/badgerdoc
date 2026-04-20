import * as React from 'react'

import { cn } from '@/helpers/utils'

interface CardProps extends React.ComponentProps<'div'> {
  hoverable?: boolean
}

function Card({ className, hoverable = false, ...props }: CardProps) {
  return (
    <div
      data-slot="card"
      className={cn(
        'bg-card text-card-foreground flex flex-col rounded-xl border border-border',
        hoverable &&
          'transition-all duration-200 hover:shadow-soft-md hover:border-border/80 hover:-translate-y-0.5',
        className
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="card-header"
      className={cn('flex flex-col gap-1.5 p-6 pb-0', className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="card-title"
      className={cn('font-heading text-lg font-semibold leading-tight tracking-tight', className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<'div'>) {
  return <div data-slot="card-content" className={cn('p-6 pt-4', className)} {...props} />
}

export { Card, CardHeader, CardTitle, CardContent }
