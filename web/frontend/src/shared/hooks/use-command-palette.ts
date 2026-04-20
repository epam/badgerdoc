import { create } from 'zustand'
import { useNavigate } from '@tanstack/react-router'
import { useCallback, useMemo, type ComponentType } from 'react'
import { useUIStore } from './use-ui-store'

export interface Command {
  id: string
  label: string
  description?: string
  icon?: ComponentType<{ className?: string }>
  shortcut?: string
  category: 'navigation' | 'actions' | 'filters' | 'views' | 'settings'
  action: () => void
  keywords?: string[]
}

interface CommandPaletteState {
  isOpen: boolean
  query: string
  open: () => void
  close: () => void
  toggle: () => void
  setQuery: (query: string) => void
}

const useCommandPaletteStore = create<CommandPaletteState>((set) => ({
  isOpen: false,
  query: '',
  open: () => set({ isOpen: true, query: '' }),
  close: () => set({ isOpen: false, query: '' }),
  toggle: () => set((state) => ({ isOpen: !state.isOpen, query: '' })),
  setQuery: (query) => set({ query }),
}))

// Fuzzy search matching
function fuzzyMatch(text: string, query: string): boolean {
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()

  // Direct substring match
  if (lowerText.includes(lowerQuery)) return true

  // Character-by-character fuzzy match
  let queryIndex = 0
  for (let i = 0; i < lowerText.length && queryIndex < lowerQuery.length; i++) {
    if (lowerText[i] === lowerQuery[queryIndex]) {
      queryIndex++
    }
  }
  return queryIndex === lowerQuery.length
}

function scoreMatch(text: string, query: string): number {
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()

  // Exact match gets highest score
  if (lowerText === lowerQuery) return 100

  // Starts with query gets high score
  if (lowerText.startsWith(lowerQuery)) return 80

  // Contains query as substring
  if (lowerText.includes(lowerQuery)) return 60

  // Fuzzy match gets lower score
  return 40
}

function useCommands(): Command[] {
  const navigate = useNavigate()
  const { setTheme, theme, toggleSidebarCollapsed } = useUIStore()

  return useMemo(
    () => [
      // Navigation commands
      {
        id: 'nav-documents',
        label: 'Go to Documents',
        description: 'Search and browse all documents',
        category: 'navigation',
        keywords: ['search', 'files', 'browse'],
        action: () => navigate({ to: '/documents' }),
      },
      {
        id: 'nav-upload',
        label: 'Upload Document',
        description: 'Upload new documents',
        category: 'navigation',
        keywords: ['new', 'add', 'import'],
        action: () => navigate({ to: '/upload' }),
      },

      // View commands
      {
        id: 'view-toggle-sidebar',
        label: 'Toggle Sidebar',
        description: 'Collapse or expand the sidebar',
        category: 'views',
        keywords: ['collapse', 'expand', 'menu'],
        action: () => toggleSidebarCollapsed(),
      },

      // Settings commands
      {
        id: 'settings-dark-mode',
        label: theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode',
        description: 'Toggle between light and dark theme',
        category: 'settings',
        shortcut: '⌘D',
        keywords: ['theme', 'appearance', 'light', 'dark'],
        action: () => setTheme(theme === 'dark' ? 'light' : 'dark'),
      },

      // Filter commands
      {
        id: 'filter-pending',
        label: 'Show Pending Documents',
        description: 'Filter to pending review items',
        category: 'filters',
        keywords: ['status', 'waiting'],
        action: () => navigate({ to: '/tasks' }),
      },
      {
        id: 'filter-extraction',
        label: 'Show Extraction Ready',
        description: 'Filter to extraction ready items',
        category: 'filters',
        keywords: ['ready', 'extract'],
        action: () => navigate({ to: '/tasks' }),
      },
      {
        id: 'filter-completed',
        label: 'Show Completed Documents',
        description: 'Filter to completed items',
        category: 'filters',
        keywords: ['done', 'finished', 'approved'],
        action: () => navigate({ to: '/tasks' }),
      },
    ],
    [navigate, setTheme, theme, toggleSidebarCollapsed]
  )
}

function useFilteredCommands(query: string): Command[] {
  const commands = useCommands()

  return useMemo(() => {
    if (!query.trim()) return commands

    const filtered = commands.filter((cmd) => {
      const searchText = [cmd.label, cmd.description || '', ...(cmd.keywords || [])].join(' ')

      return fuzzyMatch(searchText, query)
    })

    // Sort by match score
    return filtered.sort((a, b) => {
      const scoreA = scoreMatch(a.label, query)
      const scoreB = scoreMatch(b.label, query)
      return scoreB - scoreA
    })
  }, [commands, query])
}

export function useCommandPalette() {
  const store = useCommandPaletteStore()
  const filteredCommands = useFilteredCommands(store.query)

  const executeCommand = useCallback(
    (command: Command) => {
      command.action()
      store.close()
    },
    [store]
  )

  return {
    ...store,
    commands: filteredCommands,
    executeCommand,
  }
}
