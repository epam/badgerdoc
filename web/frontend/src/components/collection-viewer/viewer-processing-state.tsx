import { Button } from '@/components/ui/button'

interface ViewerProcessingStateProps {
  onRefresh: () => void
  readyPagesCount: number
  expectedPagesCount?: number | null
}

export function ViewerProcessingState({
  onRefresh,
  readyPagesCount,
  expectedPagesCount,
}: ViewerProcessingStateProps) {
  const showProgress = expectedPagesCount != null && expectedPagesCount > 0

  const progress = showProgress ? Math.round((readyPagesCount / expectedPagesCount!) * 100) : 0

  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="text-center max-w-sm w-full px-4">
        {/* Spinner */}
        <div className="flex justify-center mb-4">
          <div className="h-8 w-8 rounded-full border-2 border-gray-300 border-t-black animate-spin" />
        </div>

        {/* Title */}
        <h3 className="text-lg font-medium mb-2">Processing document…</h3>

        {/* Description */}
        <p className="text-sm text-gray-500 mb-4">
          We’re extracting pages and analyzing the content
        </p>

        {/* Progress */}
        {showProgress && (
          <div className="mb-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>
                {readyPagesCount} of {expectedPagesCount} pages ready
              </span>
              <span>{progress}%</span>
            </div>

            <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-black transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Hint */}
        <p className="text-xs text-gray-400 mb-4">This usually takes a few seconds</p>

        {/* Action */}
        <Button variant="outline" onClick={onRefresh}>
          Refresh
        </Button>
      </div>
    </div>
  )
}
