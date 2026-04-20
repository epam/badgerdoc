import { ReactNode } from 'react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'

interface SidebarTooltipProps {
  disabled?: boolean
  children: ReactNode
  text: string
}

export function SidebarTooltip({ disabled = false, children, text }: SidebarTooltipProps) {
  if (disabled) {
    return children
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild className="flex">
        {children}
      </TooltipTrigger>
      <TooltipContent side="right" className="font-semibold">
        {text}
      </TooltipContent>
    </Tooltip>
  )
}
