export function getDocumentContextTooltip(
  canUseDocumentContext: boolean,
  isWholeDocumentSelected: boolean
) {
  if (!canUseDocumentContext) {
    return 'Whole document is not available for this workflow'
  }

  return isWholeDocumentSelected ? 'Add another whole document reference' : 'Add whole document'
}

export function getCurrentPageTooltip({
  canUsePageContext,
  isCurrentPageSelected,
  currentPage,
}: {
  canUsePageContext: boolean
  isCurrentPageSelected: boolean
  currentPage: number
}) {
  if (!canUsePageContext) {
    return 'Current page context is not available for this workflow'
  }

  return isCurrentPageSelected ? `Add another Page ${currentPage} reference` : 'Add current page'
}
