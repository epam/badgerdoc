import { createFileRoute } from '@tanstack/react-router'
import { UploadPage } from '@/features/upload/page'

export const Route = createFileRoute('/upload')({
  component: UploadPage,
})
