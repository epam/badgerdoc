const LISTED_PAGES_LIMIT = 10;
const SLICE_START_INDEX = 0;
const SLICE_END_INDEX = LISTED_PAGES_LIMIT - 1;

const getPagesList = (pages: number[]) => pages?.join(', ');

const getAboveLimitPagesCount = (pages: number[]) => pages.length - LISTED_PAGES_LIMIT;

const getVisiblePagesString = (pages: number[]) => getPagesList(getVisiblePagesArray(pages));

const getVisiblePagesArray = (pages: number[]) => pages.slice(SLICE_START_INDEX, SLICE_END_INDEX);

const listRemainingPages = (pages: number[]) => {
    if (pages.length > LISTED_PAGES_LIMIT) {
        const visiblePages = getVisiblePagesString(pages);
        const remainingPagesAboveLimit = getAboveLimitPagesCount(pages);

        return `${visiblePages} and ${remainingPagesAboveLimit} more.`;
    }
    return getPagesList(pages);
};

export const createTooltip = (isExtCov: boolean, notProcessedPages: number[]): string => {
    return isExtCov
        ? `Please wait for all annotators to finish their tasks`
        : `Please validate all page to finish task. Remaining pages: ${listRemainingPages(
              notProcessedPages
          )}`;
};
