import { ReactNode, useEffect } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import {
  LayoutDashboard,
  Upload,
  PanelLeftClose,
  PanelLeft,
  Files,
  ClipboardList,
} from 'lucide-react'
import { cn } from '@/helpers/utils'
import { Button } from '@/components/ui/button'
import { TooltipProvider } from '@/components/ui/tooltip'
import { CommandPalette } from '@/components/command-palette'
import { useUIStore } from '@/shared/hooks/use-ui-store'
import { useAuth } from '@/core/auth/hooks'
import { BadgerdocLogo } from '@/components/brand/badgerdoc-logo'
import { UserInfo } from '@/design-system/layouts/user-info'
import { SidebarTooltip } from '@/design-system/layouts/sidebar-tooltip'

interface PageLayoutProps {
  children: ReactNode
}

interface NavItem {
  path: string
  label: string
  icon: typeof LayoutDashboard
}

const navItems: NavItem[] = [
  { path: '/documents', label: 'Documents', icon: Files },
  { path: '/tasks', label: 'Tasks', icon: ClipboardList },
  { path: '/upload', label: 'Upload', icon: Upload },
]

export function PageLayout({ children }: PageLayoutProps) {
  const location = useLocation()
  const { sidebarCollapsed, toggleSidebarCollapsed, setSidebarCollapsed } = useUIStore()
  const { user, login, isLoading, isAuthenticated, getCurrentUserData } = useAuth()

  useEffect(
    function onMount() {
      void getCurrentUserData()
    },
    [getCurrentUserData]
  )

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex min-h-screen bg-muted/30">
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-200 ease-out translate-x-0 lg:sticky lg:top-0 lg:h-screen',
            sidebarCollapsed ? 'w-[72px]' : 'w-64'
          )}
        >
          <div className="flex h-14 items-center justify-between border-b border-border px-4">
            <Link
              to="/documents"
              className="flex items-center gap-3 rounded-xl px-2 py-2 transition-all hover:bg-muted"
            >
              <BadgerdocLogo className="h-7 w-7" />
              <span
                className={cn(
                  'font-heading text-xl font-bold text-foreground transition-all duration-200',
                  sidebarCollapsed && 'hidden w-0 opacity-0'
                )}
              >
                Badgerdoc
              </span>
            </Link>
          </div>

          <nav className="flex-1 min-h-0 overflow-y-auto space-y-1 p-3 overflow-x-hidden">
            {navItems.map((item) => {
              const isActive =
                item.path === '/'
                  ? location.pathname === '/'
                  : location.pathname === item.path || location.pathname.startsWith(item.path + '/')

              return (
                <SidebarTooltip key={item.path} disabled={!sidebarCollapsed} text={item.label}>
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                      sidebarCollapsed && 'justify-center px-2',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )}
                    onClick={() => {
                      if (window.innerWidth < 1024) {
                        setSidebarCollapsed(true)
                      }
                    }}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    <span
                      className={cn(
                        'flex-1 transition-all duration-200',
                        sidebarCollapsed && 'hidden w-0 opacity-0'
                      )}
                    >
                      {item.label}
                    </span>
                  </Link>
                </SidebarTooltip>
              )
            })}
          </nav>

          <div className="shrink-0 border-t border-border p-3">
            <UserInfo
              user={user}
              iconOnlyMode={sidebarCollapsed}
              isLoading={isLoading}
              isAuthenticated={isAuthenticated}
              login={login}
            />
          </div>

          <div className="shrink-0 border-t border-border p-2 block">
            <SidebarTooltip disabled={!sidebarCollapsed} text="Expand sidebar">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'w-full text-muted-foreground hover:bg-muted hover:text-foreground',
                  sidebarCollapsed ? 'justify-center px-2' : 'justify-start'
                )}
                onClick={toggleSidebarCollapsed}
              >
                {sidebarCollapsed ? (
                  <PanelLeft className="h-4 w-4" />
                ) : (
                  <>
                    <PanelLeftClose className="h-4 w-4" />
                    <span className="ml-2">Collapse</span>
                  </>
                )}
              </Button>
            </SidebarTooltip>
          </div>
        </aside>

        {!sidebarCollapsed && (
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
            onClick={toggleSidebarCollapsed}
          />
        )}

        <div className="ml-[72px] lg:ml-0 flex flex-1 flex-col min-w-0 overflow-hidden">
          <main className="flex-1 overflow-hidden py-2 px-4">{children}</main>
        </div>

        {/* Command Palette */}
        <CommandPalette />
      </div>
    </TooltipProvider>
  )
}
