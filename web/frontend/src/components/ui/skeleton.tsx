import { HTMLAttributes } from 'react'
import { cn } from '@/helpers/utils'

type SkeletonVariant = 'default' | 'text' | 'title' | 'avatar' | 'button' | 'card'

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant
  shimmer?: boolean
}

const variantClasses: Record<SkeletonVariant, string> = {
  default: 'rounded-md',
  text: 'h-4 rounded',
  title: 'h-6 rounded',
  avatar: 'h-10 w-10 rounded-full',
  button: 'h-10 w-24 rounded-xl',
  card: 'h-32 rounded-xl',
}

function Skeleton({ className, variant = 'default', shimmer = true, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'bg-muted',
        variantClasses[variant],
        shimmer &&
          'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
        !shimmer && 'animate-pulse',
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
