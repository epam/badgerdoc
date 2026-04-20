import { createFileRoute } from '@tanstack/react-router'
import { DocumentsListPage } from '@/features/documents-list/page'

export const Route = createFileRoute('/documents/')({
  component: DocumentsListPage,
})
