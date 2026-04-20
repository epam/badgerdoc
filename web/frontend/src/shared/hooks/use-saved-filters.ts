import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface SavedFilter {
  id: string
  name: string
  isDefault: boolean
  createdAt: string
  filters: {
    query: string
    activeTab: string
    sortBy: string
    typeFilter: string
    dateFrom: string | null
    dateTo: string | null
  }
}

interface SavedFiltersState {
  filters: SavedFilter[]
  addFilter: (filter: Omit<SavedFilter, 'id' | 'createdAt'>) => void
  removeFilter: (id: string) => void
  setDefault: (id: string) => void
  clearDefault: () => void
  getDefault: () => SavedFilter | undefined
}

function generateId() {
  return Math.random().toString(36).substring(2, 9)
}

const useSavedFiltersStore = create<SavedFiltersState>()(
  persist(
    (set, get) => ({
      filters: [
        // Built-in presets
        {
          id: 'preset-recent-review',
          name: 'Recent Review',
          isDefault: false,
          createdAt: new Date().toISOString(),
          filters: {
            query: '',
            activeTab: 'all',
            sortBy: 'newest',
            typeFilter: 'all',
            dateTo: null,
            dateFrom: null,
          },
        },
        {
          id: 'preset-needs-attention',
          name: 'Needs Attention',
          isDefault: false,
          createdAt: new Date().toISOString(),
          filters: {
            query: '',
            activeTab: 'pending_review',
            sortBy: 'oldest',
            typeFilter: 'all',
            dateTo: null,
            dateFrom: null,
          },
        },
        {
          id: 'preset-patents-only',
          name: 'Patents Only',
          isDefault: false,
          createdAt: new Date().toISOString(),
          filters: {
            query: '',
            activeTab: 'all',
            sortBy: 'newest',
            typeFilter: 'patent',
            dateTo: null,
            dateFrom: null,
          },
        },
      ],

      addFilter: (filter) => {
        const newFilter: SavedFilter = {
          ...filter,
          id: generateId(),
          createdAt: new Date().toISOString(),
        }

        set((state) => ({
          filters: [
            ...state.filters.map((f) => ({
              ...f,
              isDefault: filter.isDefault ? false : f.isDefault,
            })),
            newFilter,
          ],
        }))
      },

      removeFilter: (id) => {
        set((state) => ({
          filters: state.filters.filter((f) => f.id !== id),
        }))
      },

      setDefault: (id) => {
        set((state) => ({
          filters: state.filters.map((f) => ({
            ...f,
            isDefault: f.id === id,
          })),
        }))
      },

      clearDefault: () => {
        set((state) => ({
          filters: state.filters.map((f) => ({
            ...f,
            isDefault: false,
          })),
        }))
      },

      getDefault: () => {
        return get().filters.find((f) => f.isDefault)
      },
    }),
    {
      name: 'hitl-saved-filters',
    }
  )
)

export function useSavedFilters() {
  const store = useSavedFiltersStore()

  return {
    savedFilters: store.filters,
    addFilter: store.addFilter,
    removeFilter: store.removeFilter,
    setDefault: store.setDefault,
    clearDefault: store.clearDefault,
    defaultFilter: store.getDefault(),
  }
}
