import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';
import TaskDocumentPages from 'components/task/task-document-pages/task-document-pages';
import TaskSidebar from 'components/task/task-sidebar/task-sidebar';
import { TaskAnnotatorContextProvider } from 'connectors/task-annotator-connector/task-annotator-context';
import { matchPath, useHistory, useLocation, useParams } from 'react-router-dom';
import { Button, Panel, Text, FlexCell, FlexRow, PickerInput } from '@epam/loveship';
import { ApiError } from 'api/api-error';
import { useNotifications } from 'shared/components/notifications';
import { TableAnnotatorContextProvider } from '../../shared/components/annotator/context/table-annotator-context';
import { DASHBOARD_PAGE, JOBS_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants/general';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';
import { useNextAndPreviousTask, useSetTaskState, useTaskById } from 'api/hooks/tasks';
import { getError } from 'shared/helpers/get-error';
import { ANNOTATION_PAGE } from 'shared/constants/general';
import styles from './task-page.module.scss';
import { FlowSideBar } from 'components/task/task-sidebar-flow/task-sidebar-flow';
import { DocumentScale } from 'components/documents/document-scale/document-scale';
import { PickGridType } from './picker-grid-type/picker-grid-type';
import { GridVariants } from 'shared/constants/task';
import { useArrayDataSource } from '@epam/uui';
import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { Labels } from 'shared/components/labels';
import { FlexSpacer } from '@epam/uui-components';

const TaskPage: FC = () => {
    const [additionalScale, setAdditionalScale] = useState(0);
    const [gridVariant, setGridVariant] = useState(GridVariants.horizontal);
    const [goToPage, setGoToPage] = useState(1);

    const { pathname } = useLocation();
    const { taskId } = useParams<{ taskId: string }>();
    const taskData = useTaskById({ taskId: Number(taskId) }, { enabled: Boolean(taskId) })?.data;
    const isLastPage = goToPage === taskData?.pages.length;
    const isFirstPage = goToPage === 1;

    const getPageNumbers = (pages = 1) => {
        const data: { [key: string]: any } = {};

        for (let i = 1; i <= pages; i++) {
            data[`_${i}`] = i;
        }

        return data;
    };

    const pagesDataSource = useArrayDataSource(
        {
            items: Object.values(getPageNumbers(taskData?.pages.length)),
            getId: (item) => item
        },
        []
    );

    const onPageChange = (page: any) => {
        setGoToPage(page);
    };

    const handleGoNext = useCallback(() => {
        isLastPage ? setGoToPage(taskData?.pages.length) : setGoToPage((prev) => prev + 1);
    }, [goToPage, taskData?.pages, isLastPage]);

    const handleGoPrev = useCallback(() => {
        isFirstPage ? setGoToPage(1) : setGoToPage((prev) => prev - 1);
    }, [goToPage, taskData?.pages, isFirstPage]);

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
                        <FlexRow spacing="12" cx={styles['full-width']}>
                            <FlexCell width="auto" minWidth={320}>
                                <BreadcrumbNavigation breadcrumbs={crumbs} />
                            </FlexCell>
                            <FlexCell width="100%">
                                <FlexRow>
                                    <Labels />
                                    <FlexSpacer />
                                    <FlexRow cx={styles['goto-page-selector']}>
                                        <FlexCell minWidth={60}>
                                            <span>Go to page</span>
                                        </FlexCell>
                                        <PickerInput
                                            minBodyWidth={52}
                                            size="24"
                                            dataSource={pagesDataSource}
                                            value={goToPage}
                                            onValueChange={onPageChange}
                                            getName={(item) => String(item)}
                                            selectionMode="single"
                                            disableClear={true}
                                        />
                                        <FlexRow>
                                            <span>of {taskData?.pages.length}</span>
                                            <Button
                                                size="24"
                                                fill="white"
                                                icon={goPrevIcon}
                                                cx={styles.button}
                                                onClick={handleGoPrev}
                                                isDisabled={isFirstPage}
                                            />
                                            <Button
                                                size="24"
                                                fill="white"
                                                icon={goNextIcon}
                                                cx={styles.button}
                                                onClick={handleGoNext}
                                                isDisabled={isLastPage}
                                            />
                                        </FlexRow>
                                    </FlexRow>
                                    <DocumentScale
                                        scale={additionalScale}
                                        onChange={setAdditionalScale}
                                    />
                                </FlexRow>
                            </FlexCell>
                        </FlexRow>
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
                            goToPage={goToPage}
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
