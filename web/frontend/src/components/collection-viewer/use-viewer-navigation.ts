import { Dispatch, SetStateAction, useCallback } from 'react'

interface Navigation {
  totalPages: number
  handlePrevClick: () => void
  handleNextClick: () => void
  handleFitToPage: () => void
}

export const useViewerNavigation = (
  totalPages: number = 0,
  currentPage: number,
  onPageChange: Dispatch<SetStateAction<number>>
): Navigation => {
  const fitPageToViewport = useCallback(
    (page: number) => {
      onPageChange(() => page)
    },
    [onPageChange]
  )

  const handleFitToPage = useCallback(() => {
    fitPageToViewport(currentPage)
  }, [fitPageToViewport, currentPage])

  const handlePrevClick = useCallback(() => {
    onPageChange((prevPage) => (prevPage === 1 ? totalPages : prevPage - 1))
  }, [totalPages, onPageChange])

  const handleNextClick = useCallback(() => {
    onPageChange((prevPage) => (prevPage === totalPages ? 1 : prevPage + 1))
  }, [totalPages, onPageChange])

  return {
    handlePrevClick,
    handleNextClick,
    handleFitToPage,
    totalPages: totalPages,
  }
}
