import { useMemo } from 'react'
import { BadgerDocExtractionPage } from '@/shared/api/badgerdoc'
import { formatExtractionContentForEditor } from '@/features/workspace/helpers/extraction-utils'

export function useFormattedExtractionContent(extractionPages?: BadgerDocExtractionPage[]) {
  return useMemo(() => formatExtractionContentForEditor(extractionPages), [extractionPages])
}
