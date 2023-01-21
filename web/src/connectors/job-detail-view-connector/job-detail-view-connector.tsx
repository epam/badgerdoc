import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useJobById } from 'api/hooks/jobs';
import { FileDocument, User } from 'api/typings';
import { usePageTable } from 'shared';
import { DataColumnProps, INotification, useUuiContext } from '@epam/uui';
import {
    TabButton,
    FlexRow,
    Panel,
    ErrorNotification,
    Text,
    SuccessNotification
} from '@epam/loveship';
import { JobDetailViewHeader } from '../../shared/components/job/job-detail-view-header';
import { useDocumentsInJob } from '../../api/hooks/documents';
import { useDistributeTasksMutation, useTasksForJob, useUsersForTask } from '../../api/hooks/tasks';
import { ApiTask, Task } from '../../api/typings/tasks';
import tasksColumn from './job-tasks-column';
import filesColumn from './job-files-columns';
import { CreateTask } from 'connectors/tasks';
import { noop } from 'lodash';
import { useStartJobMutation } from 'api/hooks/annotations';
import { getError } from 'shared/helpers/get-error';
import { datasets } from 'api/mocks/datatsets';
import { useNotifications } from 'shared/components/notifications';
import { useAsyncSourceTable } from '../../shared/hooks/async-source-table';
import { JobTable } from '../../shared/components/job/job-table-component';
import { Job } from 'api/typings/jobs';
import qs from 'qs';
import { ANNOTATION_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants';
import { useHistory } from 'react-router-dom';

type JobDetailViewProps = {
    jobId: number;
    user?: User;
    onEditJobClick: (job: Job) => void;
    getActiveTab: (tab: string) => void;
    onRowClick: (id: number) => void;
    onTaskClick: (id: number) => void;
};

export const JobConnector: React.FC<JobDetailViewProps> = ({
    jobId,
    user,
    onEditJobClick,
    getActiveTab
}) => {
    const { pageConfig, onPageChange, totalCount, searchText, tableValue, onTableValueChange } =
        usePageTable<FileDocument>('original_name');

    const history = useHistory();

    const handleExtractionJobClick = (id: number) => {
        history.push({
            pathname: `/documents/${id}`,
            search: qs.stringify({ jobId }),
            state: {
                previousPage: PREVIOUS_PAGE_JOB,
                previousPageUrl: history.location.pathname,
                previousPageName: job?.name
            }
        });
    };

    const handleTaskClick = (id: number) => {
        history.push({
            pathname: `${ANNOTATION_PAGE}/${id}`,
            search: qs.stringify({ jobId }),
            state: {
                previousPage: PREVIOUS_PAGE_JOB,
                previousPageUrl: history.location.pathname,
                previousPageName: job?.name
            }
        });
    };

    const {
        onPageChange: onTaskPageChange,
        totalCount: totalTaskCount,
        tableValue: taskTableValue,
        onTableValueChange: onTaskTableValueChange
    } = usePageTable<Task>('id');

    const { page, pageSize } = pageConfig;

    const [filesIds, setFilesIds] = useState<Array<number>>([]);
    const [tabValue, onTabValueChange] = useState('Files');
    const tabValueReference = useRef(tabValue);
    tabValueReference.current = tabValue;

    useEffect(() => {
        getActiveTab(tabValue);
    }, [tabValue]);

    const { data: job, refetch: refetchJob } = useJobById({ jobId }, { refetchInterval: 10000 });

    const svc = useUuiContext();
    const { notifyError, notifySuccess } = useNotifications();

    const { data: files, isFetching: fetchingFiles } = useDocumentsInJob(
        {
            page,
            filesIds,
            size: pageSize,
            searchText
        },
        { cacheTime: 0 }
    );

    const {
        data: tasks,
        refetch: refetchTasks,
        isFetching: taskFetching
    } = useTasksForJob(
        {
            user_id: user?.id,
            page,
            size: pageSize,
            jobId,
            jobType: job?.type
        },
        { cacheTime: 0 }
    );

    const startJobMutation = useStartJobMutation();

    useEffect(() => {
        if (job?.files) {
            setFilesIds(job.files);
        }
    }, [job, setFilesIds]);

    const { dataSource: filesDataSource } = useAsyncSourceTable<FileDocument, number>(
        fetchingFiles,
        files?.data ?? [],
        page,
        pageSize,
        filesIds,
        searchText
    );

    const { dataSource: taskDataSource } = useAsyncSourceTable<ApiTask, number>(
        taskFetching,
        tasks?.data ?? [],
        page,
        pageSize,
        jobId,
        user?.id,
        tasks
    );

    const taskView = taskDataSource.useView(taskTableValue, onTaskTableValueChange, {
        getRowOptions: (item: ApiTask) => ({
            isSelectable: true,
            onClick: () => {
                if (tabValueReference.current === 'Tasks') {
                    handleTaskClick(item.id);
                }
            }
        })
    });

    const filesView = filesDataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: (item: FileDocument) => ({
            isSelectable: true,
            onClick: () => {
                if (tabValue === 'Files') {
                    handleExtractionJobClick(item.id);
                }
            }
        })
    });

    const columnsFiles: DataColumnProps<FileDocument>[] = useMemo(() => {
        return filesColumn;
    }, []);
    const columnsTasks: DataColumnProps<ApiTask>[] = useMemo(() => {
        return tasksColumn;
    }, []);

    const { data: users } = useUsersForTask({ jobId }, {});

    const distributeTaskMutation = useDistributeTasksMutation();

    const onDistributeTaskClick = useCallback(async () => {
        try {
            if (job && users) {
                await distributeTaskMutation.mutateAsync({ job, datasets, users });
                notifySuccess(<Text>Success</Text>);
            }
        } catch (error) {
            notifyError(<Text>{getError(error)}</Text>);
        }
    }, [job]);

    const onCreateNewTaskClick = useCallback(async () => {
        svc.uuiModals
            .show((props) => (
                <CreateTask
                    {...props}
                    jobId={job?.id}
                    annotatorIds={job?.annotators || []}
                    fileIds={job?.files || []}
                />
            ))
            .then(noop)
            .catch(noop);
    }, [job]);
    const onStartJob = async () => {
        try {
            await startJobMutation.mutateAsync({ jobId });
            refetchTasks();
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <SuccessNotification {...props}>
                        <Text>Job started successfully!</Text>
                    </SuccessNotification>
                ),
                { duration: 2 }
            );
            refetchJob();
        } catch (err: any) {
            const error = err as Error;
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(error)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
        }
    };
    return (
        <>
            <Panel>
                <JobDetailViewHeader
                    type={job?.type || ''}
                    name={job?.name ? job.name : ''}
                    onCreateNewTaskClick={onCreateNewTaskClick}
                    onStartJob={onStartJob}
                    onEditJobClick={onEditJobClick}
                    job={job}
                    onDistributeTaskClick={onDistributeTaskClick}
                />
                <FlexRow vPadding={'12'}>
                    <TabButton
                        caption={'Files'}
                        isLinkActive={tabValue === 'Files'}
                        onClick={() => onTabValueChange('Files')}
                        size="36"
                    />
                    {job?.type === 'AnnotationJob' ||
                    job?.type === 'ExtractionWithAnnotationJob' ? (
                        <TabButton
                            caption="Tasks"
                            isLinkActive={tabValue === 'Tasks'}
                            onClick={() => onTabValueChange('Tasks')}
                            size="36"
                        />
                    ) : (
                        false
                    )}
                </FlexRow>
                {tabValue === `Files` ? (
                    <JobTable
                        page={page}
                        size={pageSize}
                        view={filesView}
                        value={tableValue}
                        onValueChange={onTableValueChange}
                        columns={columnsFiles}
                        totalCount={totalCount}
                        onPageChange={onPageChange}
                    />
                ) : (
                    <JobTable
                        page={pageConfig.page}
                        size={pageConfig.pageSize}
                        view={taskView}
                        value={taskTableValue}
                        onValueChange={onTaskTableValueChange}
                        columns={columnsTasks}
                        totalCount={totalTaskCount}
                        onPageChange={onTaskPageChange}
                    />
                )}
            </Panel>
        </>
    );
};
