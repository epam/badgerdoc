import { JobStatus } from 'api/typings/jobs';
import { ModelStatus } from 'api/typings/models';
import { TaskStatus, ValidationPageStatus } from 'api/typings/tasks';

export const mapStatusForJobs = (status: JobStatus, mode: string) => {
    let titleInProgress;

    if (status === 'In Progress') {
        titleInProgress =
            mode === 'Automatic' ? 'Extraction In Progress' : 'Annotation In Progress';
    } else {
        titleInProgress = status;
    }

    const statusesForJobs: Record<string, Record<string, string>> = {
        Pending: { title: status, color: 'pending' },
        'In Progress': { title: titleInProgress, color: 'progress' },
        Failed: { title: status, color: 'failed' },
        Finished: { title: status, color: 'success' },
        Draft: { title: status, color: 'pending' },
        'Ready For Annotation': { title: status, color: 'progress' }
    };

    return statusesForJobs[status] || { title: status, color: 'default' };
};

export const mapStatusForModels = (status: ModelStatus) => {
    const statusesForModels = {
        deployed: { color: 'success' },
        ready: { color: 'progress' },
        failed: { color: 'failed' },
        deploying: { color: 'success' }
    };

    return statusesForModels[status] || { color: 'default' };
};

export const mapStatusForTasks = (status: TaskStatus) => {
    const statusesForTasks = {
        Pending: { title: status, color: 'pending' },
        'In Progress': { title: status, color: 'progress' },
        Ready: { title: status, color: 'failed' },
        Finished: { title: status, color: 'success' }
    };

    return statusesForTasks[status] || { color: 'default' };
};

export const mapStatusForValidationPage = (status: ValidationPageStatus) => {
    const statusesForValidationPage = {
        'Invalid Page': { title: status, color: 'failed' },
        'Valid Page': { title: status, color: 'success' }
    };

    return statusesForValidationPage[status] || { color: 'default' };
};
