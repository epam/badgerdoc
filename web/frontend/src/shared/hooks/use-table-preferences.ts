import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface TableColumn {
  id: string
  label: string
  defaultVisible: boolean
  sortable?: boolean
  width?: string
  minWidth?: string
}

// Available columns for the document table
const documentColumns: TableColumn[] = [
  { id: 'select', label: 'Select', defaultVisible: true, sortable: false, width: '40px' },
  { id: 'title', label: 'Title', defaultVisible: true, sortable: true, minWidth: '200px' },
  { id: 'type', label: 'Type', defaultVisible: true, sortable: true, width: '100px' },
  { id: 'status', label: 'Status', defaultVisible: true, sortable: true, width: '130px' },
  { id: 'confidence', label: 'Confidence', defaultVisible: true, sortable: true, width: '110px' },
  { id: 'authors', label: 'Authors', defaultVisible: false, sortable: true, minWidth: '150px' },
  { id: 'date', label: 'Date', defaultVisible: true, sortable: true, width: '100px' },
  { id: 'created', label: 'Created', defaultVisible: false, sortable: true, width: '100px' },
  { id: 'aging', label: 'Aging', defaultVisible: false, sortable: true, width: '80px' },
  { id: 'priority', label: 'Priority', defaultVisible: false, sortable: true, width: '90px' },
  { id: 'quality', label: 'Quality', defaultVisible: false, sortable: true, width: '90px' },
  { id: 'assignee', label: 'Assignee', defaultVisible: false, sortable: true, width: '120px' },
  { id: 'actions', label: 'Actions', defaultVisible: true, sortable: false, width: '80px' },
]

interface TablePreferencesState {
  // Column visibility per table
  columnVisibility: Record<string, Record<string, boolean>>

  // Column order per table
  columnOrder: Record<string, string[]>

  // Actions
  setColumnVisibility: (tableId: string, columnId: string, visible: boolean) => void
  setAllColumnVisibility: (tableId: string, visibility: Record<string, boolean>) => void
  setColumnOrder: (tableId: string, order: string[]) => void
  getVisibleColumns: (tableId: string, availableColumns: TableColumn[]) => TableColumn[]
  getColumnOrder: (tableId: string, availableColumns: TableColumn[]) => string[]
  resetToDefaults: (tableId: string, availableColumns: TableColumn[]) => void
}

const useTablePreferencesStore = create<TablePreferencesState>()(
  persist(
    (set, get) => ({
      columnVisibility: {},
      columnOrder: {},

      setColumnVisibility: (tableId, columnId, visible) => {
        set((state) => ({
          columnVisibility: {
            ...state.columnVisibility,
            [tableId]: {
              ...state.columnVisibility[tableId],
              [columnId]: visible,
            },
          },
        }))
      },

      setAllColumnVisibility: (tableId, visibility) => {
        set((state) => ({
          columnVisibility: {
            ...state.columnVisibility,
            [tableId]: visibility,
          },
        }))
      },

      setColumnOrder: (tableId, order) => {
        set((state) => ({
          columnOrder: {
            ...state.columnOrder,
            [tableId]: order,
          },
        }))
      },

      getVisibleColumns: (tableId, availableColumns) => {
        const visibility = get().columnVisibility[tableId] || {}
        const order = get().columnOrder[tableId] || availableColumns.map((c) => c.id)

        // Get columns that are visible
        const visibleColumnIds = availableColumns
          .filter((col) => {
            // Use stored visibility if set, otherwise use default
            return visibility[col.id] !== undefined ? visibility[col.id] : col.defaultVisible
          })
          .map((c) => c.id)

        // Sort by order preference
        const orderedIds = order.filter((id) => visibleColumnIds.includes(id))

        // Add any visible columns that aren't in the order (new columns)
        const missingIds = visibleColumnIds.filter((id) => !orderedIds.includes(id))
        const finalOrder = [...orderedIds, ...missingIds]

        return finalOrder
          .map((id) => availableColumns.find((c) => c.id === id))
          .filter((c): c is TableColumn => c !== undefined)
      },

      getColumnOrder: (tableId, availableColumns) => {
        const stored = get().columnOrder[tableId]
        if (stored && stored.length > 0) {
          return stored
        }
        return availableColumns.map((c) => c.id)
      },

      resetToDefaults: (tableId, availableColumns) => {
        const defaultVisibility: Record<string, boolean> = {}
        availableColumns.forEach((col) => {
          defaultVisibility[col.id] = col.defaultVisible
        })

        set((state) => ({
          columnVisibility: {
            ...state.columnVisibility,
            [tableId]: defaultVisibility,
          },
          columnOrder: {
            ...state.columnOrder,
            [tableId]: availableColumns.map((c) => c.id),
          },
        }))
      },
    }),
    {
      name: 'table-preferences-storage',
    }
  )
)

// Hook for convenient use with a specific table
export function useTablePreferences(
  tableId: string,
  availableColumns: TableColumn[] = documentColumns
) {
  const store = useTablePreferencesStore()

  return {
    visibleColumns: store.getVisibleColumns(tableId, availableColumns),
    columnOrder: store.getColumnOrder(tableId, availableColumns),
    allColumns: availableColumns,
    isColumnVisible: (columnId: string) => {
      const visibility = store.columnVisibility[tableId]
      if (visibility && visibility[columnId] !== undefined) {
        return visibility[columnId]
      }
      const col = availableColumns.find((c) => c.id === columnId)
      return col?.defaultVisible ?? true
    },
    toggleColumn: (columnId: string) => {
      const currentlyVisible =
        store.columnVisibility[tableId]?.[columnId] ??
        availableColumns.find((c) => c.id === columnId)?.defaultVisible ??
        true
      store.setColumnVisibility(tableId, columnId, !currentlyVisible)
    },
    setColumnVisibility: (columnId: string, visible: boolean) => {
      store.setColumnVisibility(tableId, columnId, visible)
    },
    reorderColumns: (newOrder: string[]) => {
      store.setColumnOrder(tableId, newOrder)
    },
    resetToDefaults: () => {
      store.resetToDefaults(tableId, availableColumns)
    },
  }
}
