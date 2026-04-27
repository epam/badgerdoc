import { Button } from '@/components/ui/button'

interface ViewerProcessingStateProps {
  onRefresh: () => void
}

export function ViewerProcessingState({ onRefresh }: ViewerProcessingStateProps) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="text-center max-w-sm">
        <h3 className="text-lg font-medium mb-2">Document is being processed</h3>

        <p className="text-sm text-gray-500 mb-4">
          Pages are not ready yet. Please wait a moment or refresh.
        </p>

        <Button variant="outline" onClick={onRefresh}>
          Refresh
        </Button>
      </div>
    </div>
  )
}
