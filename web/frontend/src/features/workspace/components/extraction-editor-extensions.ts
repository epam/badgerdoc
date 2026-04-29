import StarterKit from '@tiptap/starter-kit'
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import { Table, TableCell, TableHeader, TableRow } from '@tiptap/extension-table'
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

export function createExtractionTableExtensions() {
  return [
    StarterKit.configure({ document: false, paragraph: false }),
    ExtractionDocument,
    OcrParagraph,
    Table.configure(TableKitStylingConfig.table),
    TableRow.configure(TableKitStylingConfig.tableRow),
    TableHeader.configure(TableKitStylingConfig.tableHeader),
    TableCell.configure(TableKitStylingConfig.tableCell),
    Subscript,
    Superscript,
  ]
}
