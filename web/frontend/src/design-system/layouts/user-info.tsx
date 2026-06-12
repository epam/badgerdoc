import { cn } from '@/helpers/utils'
import { LogIn } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SidebarTooltip } from '@/design-system/layouts/sidebar-tooltip'

interface UserInfoProps {
  isAuthenticated: boolean
  isLoading: boolean
  iconOnlyMode: boolean
  user: { name?: string | null; role?: string | null } | null
  login: () => void
}

export function UserInfo({ isAuthenticated, isLoading, iconOnlyMode, user, login }: UserInfoProps) {
  /** Show user info when available */
  if (isAuthenticated && user && !isLoading) {
    return (
      <SidebarTooltip disabled={!iconOnlyMode} text={`${user.name} (${user.role})`}>
        <div
          className={cn(
            'flex items-center gap-3 rounded-xl p-2 transition-all duration-150 hover:bg-muted',
            iconOnlyMode && 'justify-center p-1'
          )}
        >
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium text-foreground">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div
            className={cn(
              'flex-1 truncate transition-all duration-200',
              iconOnlyMode && 'hidden w-0 opacity-0'
            )}
          >
            <p className="text-sm font-semibold text-foreground">{user?.name}</p>
            <p className="text-xs capitalize text-muted-foreground">{user?.role}</p>
          </div>
        </div>
      </SidebarTooltip>
    )
  }

  /** Handle scenario when auth cookies exist on app mount */
  if (isAuthenticated && isLoading) {
    return null
  }

  /** Handle scenario when user action is required for authentication */
  return (
    <SidebarTooltip disabled={!iconOnlyMode} text="Login">
      <Button
        disabled={isLoading}
        variant="ghost"
        className={cn(
          'w-full group flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-150',
          'text-muted-foreground hover:bg-muted hover:text-foreground text-left text-sm font-medium',
          iconOnlyMode && 'justify-center px-2'
        )}
        onClick={login}
      >
        <LogIn className="size-5 flex-shrink-0" />
        <span
          className={cn(
            'flex-1 transition-all duration-200',
            iconOnlyMode && 'hidden w-0 opacity-0'
          )}
        >
          Login
        </span>
      </Button>
    </SidebarTooltip>
  )
}
