import React, { FC, useEffect, useMemo, useState } from 'react';
import TaskDocumentPages from 'components/task/task-document-pages/task-document-pages';
import TaskSidebar from 'components/task/task-sidebar/task-sidebar';
import { TaskAnnotatorContextProvider } from 'connectors/task-annotator-connector/task-annotator-context';
import { matchPath, useHistory, useLocation, useParams } from 'react-router-dom';
import { Button, Panel, Text } from '@epam/loveship';
import { ApiError } from 'api/api-error';
import { useNotifications } from 'shared/components/notifications';
import { TableAnnotatorContextProvider } from '../../shared/components/annotator/context/table-annotator-context';
import { DASHBOARD_PAGE, JOBS_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants/general';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';
import { useNextAndPreviousTask, useSetTaskState } from 'api/hooks/tasks';
import { getError } from 'shared/helpers/get-error';
import { ANNOTATION_PAGE } from 'shared/constants/general';
import styles from './task-page.module.scss';
import { FlowSideBar } from 'components/task/task-sidebar-flow/task-sidebar-flow';
import { DocumentScale } from 'components/documents/document-scale/document-scale';
import { PickGridType } from './picker-grid-type/picker-grid-type';
import { GridVariants } from 'shared/constants/task';

const TaskPage: FC = () => {
    const [additionalScale, setAdditionalScale] = useState(0);
    const [gridVariant, setGridVariant] = useState(GridVariants.horizontal);

    const { pathname } = useLocation();
    const { taskId } = useParams<{ taskId: string }>();
    const history = useHistory<Record<string, string | undefined>>();
    const { notifySuccess, notifyError } = useNotifications();
    const nextTaskId = useNextAndPreviousTask(taskId).data?.next_task?.id;

    useEffect(() => {
        useSetTaskState({ id: Number(taskId), eventType: 'opened' });
    }, [taskId]);

    const handleRedirectToNextTask = () => {
        const isMatch = matchPath(pathname, { path: '/tasks/:taskId' });
        const pathToRedirect = isMatch
            ? `/tasks/${nextTaskId}`
            : `${ANNOTATION_PAGE}/${nextTaskId}`;

        history.push(pathToRedirect);
    };

    const handleRedirectAfterFinish = () => {
        if (nextTaskId && localStorage.getItem('submitted-task-redirection-page') === 'next-task') {
            handleRedirectToNextTask();
            return;
        }

        history.push(DASHBOARD_PAGE);
    };

    const handleSaveTaskSuccess = () => {
        notifySuccess(<Text>Saved successfully</Text>);
    };

    const handleSaveTaskError = (error: ApiError) => {
        notifyError(
            <Panel>
                <Text>{getError(error)}</Text>
            </Panel>
        );
    };

    const crumbs = useMemo(() => {
        const crumbs = [];
        const { previousPage, previousPageName, previousPageUrl } = history.location.state ?? {};

        if (previousPage === PREVIOUS_PAGE_JOB) {
            crumbs.push({ name: 'Extractions', url: JOBS_PAGE });
            crumbs.push({
                name: previousPageName ?? '',
                url: previousPageUrl
            });
        } else {
            crumbs.push({ name: 'My Tasks', url: DASHBOARD_PAGE });
        }

        crumbs.push({ name: 'Task' });

        return crumbs;
    }, [history.location.state]);

    return (
        <TaskAnnotatorContextProvider
            taskId={Number(taskId)}
            onRedirectAfterFinish={handleRedirectAfterFinish}
            onSaveTaskSuccess={handleSaveTaskSuccess}
            onSaveTaskError={handleSaveTaskError}
        >
            <div className="flex-col">
                <div className={styles.title}>
                    <div className={styles['title__left-block']}>
                        <BreadcrumbNavigation breadcrumbs={crumbs} />
                        <DocumentScale scale={additionalScale} onChange={setAdditionalScale} />
                    </div>
                    <div className={styles['title__right-block']}>
                        <div>
                            <PickGridType value={gridVariant} onChange={setGridVariant} />
                        </div>
                        {nextTaskId && (
                            <Button
                                size="30"
                                fill="white"
                                caption="Next"
                                cx={styles['next-button']}
                                onClick={handleRedirectToNextTask}
                            />
                        )}
                    </div>
                </div>
                <div className={styles.content}>
                    <TableAnnotatorContextProvider>
                        <FlowSideBar />
                        <TaskDocumentPages
                            viewMode={false}
                            gridVariant={gridVariant}
                            additionalScale={additionalScale}
                        />
                        <TaskSidebar viewMode={false} isNextTaskPresented={Boolean(nextTaskId)} />
                    </TableAnnotatorContextProvider>
                </div>
            </div>
        </TaskAnnotatorContextProvider>
    );
};

export default TaskPage;
