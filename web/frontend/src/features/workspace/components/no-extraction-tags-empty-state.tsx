import { FileText } from 'lucide-react'

export function NoExtractionTagsEmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <FileText className="mb-4 h-12 w-12 text-muted-foreground" />
      <h3 className="text-lg font-medium">No extraction results available</h3>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        This document does not have extraction result types to review yet.
      </p>
    </div>
  )
}
