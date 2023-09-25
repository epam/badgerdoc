import { TaskStatus } from 'api/typings/tasks';
import { FINISHED_TASK_TOOLTIP_TEXT } from './finish-button/utils';

export const getSaveButtonTooltipContent = (
    isSaveButtonDisabled: boolean,
    taskStatus?: TaskStatus
) => {
    if (isSaveButtonDisabled && taskStatus === 'Finished') {
        return FINISHED_TASK_TOOLTIP_TEXT;
    } else if (isSaveButtonDisabled && taskStatus === 'Pending') {
        return null;
    } else if (isSaveButtonDisabled) {
        return 'Please modify annotation to enable save button';
    }
    return null;
};
