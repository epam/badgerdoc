import { TaskStatus } from 'api/typings/tasks';

const LISTED_PAGES_LIMIT = 10;

const getPagesList = (pages: number[]) => pages.join(', ');

const getAboveLimitPagesCount = (pages: number[]) => pages.length - LISTED_PAGES_LIMIT;

const getVisiblePagesArray = (pages: number[]) => pages.slice(0, LISTED_PAGES_LIMIT);

const getVisiblePagesString = (pages: number[]) => getPagesList(getVisiblePagesArray(pages));

const listRemainingPages = (pages: number[]) => {
    if (pages.length > LISTED_PAGES_LIMIT) {
        const visiblePages = getVisiblePagesString(pages);
        const remainingPagesAboveLimit = getAboveLimitPagesCount(pages);

        return `${visiblePages} and ${remainingPagesAboveLimit} more.`;
    }
    return getPagesList(pages);
};

interface CreateTooltipArgs {
    isExtCov: boolean;
    notProcessedPages: number[];
    isDisabled: boolean;
    taskStatus?: TaskStatus;
}

export const FINISHED_TASK_TOOLTIP_TEXT =
    'This annotation task is done. To continue annotating this document create a new task';

export const createTooltip = ({
    isDisabled,
    taskStatus,
    isExtCov,
    notProcessedPages
}: CreateTooltipArgs) => {
    switch (true) {
        case !isDisabled || taskStatus === 'Pending':
            return null;
        case taskStatus === 'Finished':
            return FINISHED_TASK_TOOLTIP_TEXT;
        default:
            return isExtCov
                ? 'Please wait for all annotators to finish their tasks'
                : `Please validate all page to finish task. Remaining pages: ${listRemainingPages(
                      notProcessedPages
                  )}`;
    }
};
