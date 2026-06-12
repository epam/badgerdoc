import StarterKit from '@tiptap/starter-kit'
import { mergeAttributes, Node } from '@tiptap/core'
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import { Table, TableCell, TableHeader, TableRow } from '@tiptap/extension-table'
import BulletList from '@tiptap/extension-bullet-list'
import OrderedList from '@tiptap/extension-ordered-list'
import ListItem from '@tiptap/extension-list-item'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'

const ExtractionDocument = Document.extend({
  content: 'extractionBlock*',
})

const OcrParagraph = Paragraph.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      htmlClass: {
        default: null,
        parseHTML: (element) => element.getAttribute('class'),
        renderHTML: (attributes) => {
          if (!attributes.htmlClass) return {}
          return { class: attributes.htmlClass }
        },
      },
    }
  },
})

const OcrSpan = Node.create({
  name: 'ocrSpan',

  group: 'inline',

  inline: true,

  content: 'inline*',

  selectable: false,

  addAttributes() {
    return {
      htmlClass: {
        default: null,
        parseHTML: (element) => element.getAttribute('class'),
        renderHTML: (attributes) => {
          if (!attributes.htmlClass) return {}
          return { class: attributes.htmlClass }
        },
      },
      htmlId: {
        default: null,
        parseHTML: (element) => element.getAttribute('id'),
        renderHTML: (attributes) => {
          if (!attributes.htmlId) return {}
          return { id: attributes.htmlId }
        },
      },
      title: {
        default: null,
        parseHTML: (element) => element.getAttribute('title'),
        renderHTML: (attributes) => {
          if (!attributes.title) return {}
          return { title: attributes.title }
        },
      },
    }
  },

  parseHTML() {
    return [{ tag: 'span' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes), 0]
  },
})

function parseCellAttrs(node: HTMLElement) {
  const colspan = Number(node.getAttribute('colspan') || 1)
  const rowspan = Number(node.getAttribute('rowspan') || 1)
  const colwidthAttr = node.getAttribute('colwidth')
  const colwidth =
    colwidthAttr && /^\d+(,\d+)*$/.test(colwidthAttr)
      ? colwidthAttr.split(',').map((width) => Number(width))
      : null

  return {
    colspan,
    rowspan,
    colwidth,
  }
}

const OcrTableHeader = TableHeader.extend({
  parseHTML() {
    return [
      {
        tag: 'th',
        getAttrs: (node) => {
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
      {
        // hOCR table fragments may contain <td> cells in <thead>; treat them as header cells.
        tag: 'thead td',
        getAttrs: (node) => {
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
    ]
  },
})

const OcrTableCell = TableCell.extend({
  parseHTML() {
    return [
      {
        // Keep body cells as regular data cells and avoid stealing thead cells.
        tag: 'tbody td',
        getAttrs: (node) => {
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
      {
        tag: 'tfoot td',
        getAttrs: (node) => {
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
      {
        // Fallback for tables without explicit tbody.
        tag: 'table > tr > td',
        getAttrs: (node) => {
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
      {
        tag: 'td',
        getAttrs: (node) => {
          const parentTag = (
            node as HTMLElement
          ).parentElement?.parentElement?.tagName?.toLowerCase()
          if (parentTag === 'thead') {
            return false
          }
          const attrs = parseCellAttrs(node as HTMLElement)
          if (attrs.colspan === 1 && attrs.rowspan === 1 && attrs.colwidth === null) {
            return null
          }
          return attrs
        },
      },
    ]
  },
})

const TableKitStylingConfig = {
  table: {
    resizable: false,
    HTMLAttributes: {
      class: 'w-full border-collapse border',
    },
  },
  tableRow: {
    HTMLAttributes: {
      class: 'border border-gray-200',
    },
  },
  tableHeader: {
    HTMLAttributes: {
      class: 'border border-gray-300 px-4 py-3 text-left font-medium text-gray-900 bg-gray-50',
    },
  },
  tableCell: {
    HTMLAttributes: {
      class: 'border border-gray-200 px-4 py-3 text-gray-700',
    },
  },
}

export const ListKitStylingConfig = {
  bulletList: {
    HTMLAttributes: {
      class: 'list-disc ml-6 space-y-1',
    },
  },

  orderedList: {
    HTMLAttributes: {
      class: 'list-decimal ml-6 space-y-1',
    },
  },

  listItem: {
    HTMLAttributes: {
      class: 'leading-relaxed',
    },
  },
}

export function createExtractionTableExtensions() {
  return [
    StarterKit.configure({
      document: false,
      paragraph: false,
      bulletList: false,
      orderedList: false,
      listItem: false,
    }),
    BulletList.configure(ListKitStylingConfig.bulletList),
    OrderedList.configure(ListKitStylingConfig.orderedList),
    ListItem.configure(ListKitStylingConfig.listItem),
    ExtractionDocument,
    OcrParagraph,
    OcrSpan,
    Table.configure(TableKitStylingConfig.table),
    TableRow.configure(TableKitStylingConfig.tableRow),
    OcrTableHeader.configure(TableKitStylingConfig.tableHeader),
    OcrTableCell.configure(TableKitStylingConfig.tableCell),
    Subscript,
    Superscript,
  ]
}
