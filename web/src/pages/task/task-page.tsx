import React, { FC } from 'react';
import TaskDocumentPages from 'components/task/task-document-pages/task-document-pages';
import TaskSidebar from 'components/task/task-sidebar/task-sidebar';
import styles from './task-page.module.scss';
import { TaskAnnotatorContextProvider } from 'connectors/task-annotator-connector/task-annotator-context';
import { useHistory, useParams } from 'react-router-dom';
import { Panel, Text } from '@epam/loveship';
import { ApiError } from 'api/api-error';
import { useNotifications } from 'shared/components/notifications';
import { TableAnnotatorContextProvider } from '../../shared/components/annotator/context/table-annotator-context';
import { DASHBOARD_PAGE, JOBS_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';

const TaskPage: FC = () => {
    const { taskId } = useParams<{ taskId: string }>();

    const history = useHistory();
    const handleRedirectAfterFinish = () => {
        return history.push(DASHBOARD_PAGE);
    };

    const { notifySuccess, notifyError } = useNotifications();

    const handleSaveTaskSuccess = () => {
        notifySuccess(<Text>Saved successfully</Text>);
    };

    const handleSaveTaskError = (error: ApiError) => {
        notifyError(
            // TODO: create component for notifications
            <Panel>
                <Text font="sans-semibold" fontSize="16" color="fire">
                    {error.message}
                </Text>
                <Text>{error.summary}</Text>
            </Panel>
        );
    };

    const historyState = history.location.state as {
        previousPage?: string;
        previousPageUrl?: string;
        previousPageName?: string;
    };
    const crumbs = [];
    if (historyState?.previousPage === PREVIOUS_PAGE_JOB) {
        crumbs.push({ name: 'Extractions', url: JOBS_PAGE });
        crumbs.push({
            name: historyState.previousPageName || '',
            url: historyState.previousPageUrl
        });
    } else {
        crumbs.push({ name: 'My Tasks', url: DASHBOARD_PAGE });
    }
    crumbs.push({ name: 'Task' });
    return (
        <TaskAnnotatorContextProvider
            taskId={Number(taskId)}
            onRedirectAfterFinish={handleRedirectAfterFinish}
            onSaveTaskSuccess={handleSaveTaskSuccess}
            onSaveTaskError={handleSaveTaskError}
        >
            <div className="flex-col">
                <div className={styles.title}>
                    <BreadcrumbNavigation breadcrumbs={crumbs} />
                </div>
                <div className={`${styles.content}`}>
                    <TableAnnotatorContextProvider>
                        <TaskDocumentPages viewMode={false} />
                        <TaskSidebar
                            onRedirectAfterFinish={handleRedirectAfterFinish}
                            viewMode={false}
                        />
                    </TableAnnotatorContextProvider>
                </div>
            </div>
        </TaskAnnotatorContextProvider>
    );
};

export default TaskPage;
