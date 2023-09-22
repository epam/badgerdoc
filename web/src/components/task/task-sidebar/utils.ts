import { TaskStatus } from 'api/typings/tasks';
import { FINISHED_TASK_TOOLTIP_TEXT } from './finish-button/utils';

export const getSaveButtonTooltipContent = (
    isSaveButtonDisabled: boolean,
    taskStatus?: TaskStatus
) => {
    switch (true) {
        case isSaveButtonDisabled && taskStatus === 'Finished':
            return FINISHED_TASK_TOOLTIP_TEXT;
        case isSaveButtonDisabled && taskStatus === 'Pending':
            return null;
        case isSaveButtonDisabled:
            return 'Please modify annotation to enable save button';
        default:
            return null;
    }
};
