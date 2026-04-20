import { useEffect, useRef, useState, useCallback, type KeyboardEvent } from 'react'
import { Command as CommandIcon, Search, ArrowRight, CornerDownLeft } from 'lucide-react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { cn } from '@/helpers/utils'
import { useCommandPalette, type Command } from '@/shared/hooks/use-command-palette'

const categoryLabels: Record<string, string> = {
  navigation: 'Navigation',
  actions: 'Actions',
  filters: 'Filters',
  views: 'Views',
  settings: 'Settings',
}

const categoryOrder = ['navigation', 'filters', 'views', 'settings', 'actions']

function groupCommandsByCategory(commands: Command[]) {
  const groups = new Map<string, Command[]>()

  for (const cmd of commands) {
    const existing = groups.get(cmd.category) || []
    groups.set(cmd.category, [...existing, cmd])
  }

  // Sort by category order
  return categoryOrder
    .filter((cat) => groups.has(cat))
    .map((cat) => ({
      category: cat,
      label: categoryLabels[cat] || cat,
      commands: groups.get(cat)!,
    }))
}

export function CommandPalette() {
  const { isOpen, query, setQuery, close, commands, executeCommand } = useCommandPalette()
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [isOpen])

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((i) => Math.min(i + 1, commands.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((i) => Math.max(i - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          if (commands[selectedIndex]) {
            executeCommand(commands[selectedIndex])
          }
          break
        case 'Escape':
          e.preventDefault()
          close()
          break
      }
    },
    [commands, selectedIndex, executeCommand, close]
  )

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selected = listRef.current.querySelector('[data-selected="true"]')
      selected?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex])

  const groupedCommands = groupCommandsByCategory(commands)

  // Calculate flat index for each command
  let flatIndex = 0
  const commandsWithIndex = groupedCommands.map((group) => ({
    ...group,
    commands: group.commands.map((cmd) => ({ ...cmd, flatIndex: flatIndex++ })),
  }))

  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && close()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-1/2 top-[15%] z-50 w-full max-w-xl -translate-x-1/2 rounded-xl border border-border bg-card shadow-2xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=open]:slide-in-from-left-1/2"
          onKeyDown={handleKeyDown}
        >
          <DialogPrimitive.Title className="sr-only">Command Palette</DialogPrimitive.Title>
          <DialogPrimitive.Description className="sr-only">
            Search for commands and navigate quickly
          </DialogPrimitive.Description>

          {/* Search input */}
          <div className="flex items-center gap-3 border-b border-border px-4">
            <Search className="h-5 w-5 text-muted-foreground" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Type a command or search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-transparent py-4 text-base outline-none placeholder:text-muted-foreground"
            />
            <kbd className="hidden rounded-md bg-muted px-2 py-1 text-xs font-mono text-muted-foreground sm:inline-block">
              ESC
            </kbd>
          </div>

          {/* Command list */}
          <div ref={listRef} className="max-h-80 overflow-y-auto overscroll-contain p-2">
            {commands.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No commands found for "{query}"
              </div>
            ) : (
              commandsWithIndex.map((group) => (
                <div key={group.category} className="mb-2">
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {group.label}
                  </div>
                  {group.commands.map((cmd) => {
                    const isSelected = cmd.flatIndex === selectedIndex
                    return (
                      <button
                        key={cmd.id}
                        data-selected={isSelected}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(cmd.flatIndex)}
                        className={cn(
                          'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
                          isSelected ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                        )}
                      >
                        <ArrowRight
                          className={cn(
                            'h-4 w-4 flex-shrink-0',
                            isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{cmd.label}</div>
                          {cmd.description && (
                            <div
                              className={cn(
                                'text-sm truncate',
                                isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'
                              )}
                            >
                              {cmd.description}
                            </div>
                          )}
                        </div>
                        {cmd.shortcut && (
                          <kbd
                            className={cn(
                              'hidden rounded px-1.5 py-0.5 text-xs font-mono sm:inline-block',
                              isSelected
                                ? 'bg-primary-foreground/20 text-primary-foreground'
                                : 'bg-muted text-muted-foreground'
                            )}
                          >
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </button>
                    )
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-border px-4 py-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono">↑↓</kbd>
                navigate
              </span>
              <span className="flex items-center gap-1">
                <CornerDownLeft className="h-3 w-3" />
                select
              </span>
            </div>
            <div className="flex items-center gap-1">
              <CommandIcon className="h-3 w-3" />
              <span>Command Palette</span>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
