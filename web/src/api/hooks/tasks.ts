import {
    Dataset,
    MutationHookType,
    Operators,
    PagedResponse,
    QueryHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    UseTasksResponseObj,
    User,
    DocumentExtraOption,
    FilterWithDocumentExtraOption
} from 'api/typings';
import { Job } from 'api/typings/jobs';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { ApiTask, Task, TaskModel, ValidationPages } from '../typings/tasks';
import { useBadgerFetch } from './api';
import { pageSizes } from '../../shared';

type UseTasksParamsType = {
    page: number;
    size: number;
    user_id?: string | null;
    sortConfig: Sorting<keyof Task>;
    filters: Array<FilterWithDocumentExtraOption<keyof Task>>;
};

type UseTasksForJobParamsType = {
    page: number;
    size: number;
    jobId: number;
    user_id?: string;
    jobType?: string;
};
type DistributeTasksParams = {
    job: Job;
    datasets: Dataset[];
    users: User[];
};

const namespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;

export const useTasks: QueryHookType<UseTasksParamsType, PagedResponse<Task>> = (
    { user_id, page, size },
    options
) =>
    useQuery(
        ['tasks', user_id, page, size],
        async () => {
            const data = await useBadgerFetch<UseTasksResponseObj>({
                url: `${namespace}/tasks?user_id=${user_id}&pagination_page_size=${size}&pagination_start_page=${page}`,
                method: 'get'
            })();

            const { annotation_tasks, total_objects, page_size, current_page } = data;

            return {
                data: annotation_tasks,
                pagination: {
                    has_more: current_page * page_size < total_objects,
                    min_pages_left: 1,
                    total: total_objects,
                    page_size,
                    page_num: current_page
                }
            };
        },
        options
    );

type TaskByIdParams = {
    taskId: number;
};

type UsersForTaskParams = {
    jobId: number;
};

export const useTaskForDashboard: QueryHookType<UseTasksParamsType, PagedResponse<Task>> = ({
    user_id,
    page,
    size,
    sortConfig,
    filters
}) =>
    useQuery(['tasks', user_id, page, size, sortConfig, filters], async () => {
        const body: SearchBody<Task> = {
            pagination: {
                page_num: page,
                page_size: size
            },
            filters: [
                {
                    field: 'user_id',
                    operator: Operators.EQ,
                    value: `${user_id}`
                },
                ...filters
            ],
            sorting: [
                sortConfig ?? {
                    field: 'id',
                    direction: SortingDirection.DESC
                }
            ]
        };
        return useBadgerFetch({
            url: `${namespace}/tasks/search`,
            method: 'post'
        })(JSON.stringify(body));
    });

export function taskPropFetcher(
    propName: keyof Task | keyof DocumentExtraOption,
    page = 1,
    size = pageSizes._15,
    keyword: string = ''
): Promise<PagedResponse<string>> {
    const sortConfig = {
        field: propName,
        direction: SortingDirection.ASC
    };
    const filters: FilterWithDocumentExtraOption<keyof Task>[] = [];
    filters.push({
        field: propName,
        operator: Operators.DISTINCT
    });
    if (keyword) {
        filters.push({
            field: propName,
            operator: Operators.ILIKE,
            value: `%${keyword}%`
        });
    }
    const body: SearchBody<Task> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field as keyof Task }]
    };

    return useBadgerFetch<PagedResponse<string>>({
        url: `${namespace}/tasks/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

const mapTaskFromApi = (apiTask: ApiTask): Task => {
    const { user, ...task } = apiTask;
    return { ...task, user_id: user.id };
};

export const useTaskById: QueryHookType<TaskByIdParams, Task> = ({ taskId }) =>
    useQuery(
        ['task', taskId],
        async () =>
            useBadgerFetch<ApiTask>({
                url: `${namespace}/tasks/${taskId}`,
                method: 'get'
            })(),
        { select: mapTaskFromApi }
    );
export const useUsersForTask: QueryHookType<UsersForTaskParams, User[]> = ({ jobId }) =>
    useQuery(['usersForTask', jobId], async () =>
        useBadgerFetch({
            url: `${namespace}/jobs/${jobId}/users`,
            method: 'get',
            withCredentials: true
        })()
    );

export const distributeTasks = async (params: DistributeTasksParams): Promise<Task[]> => {
    const requestData = {
        user_ids: params.users.map((user) => user.id),
        files: params.job?.files,
        datasets: params.datasets.map((dataset) => dataset.id),
        job_id: params.job.id
    };
    return useBadgerFetch<Task[]>({
        url: `${namespace}/distribution`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(requestData));
};

export const useDistributeTasksMutation: MutationHookType<DistributeTasksParams, Task[]> = () => {
    const queryClient = useQueryClient();
    return useMutation(distributeTasks, {
        onSuccess: () => {
            queryClient.invalidateQueries('tasks');
        }
    });
};

async function fetchTasksForJob(
    user_id: string | undefined,
    jobId: number,
    size: number,
    page: number
) {
    const newUrl = `${namespace}/tasks`;
    const searchParams = new URLSearchParams();
    if (user_id) searchParams.set(`user_id`, user_id ?? '');
    searchParams.set(`job_id`, jobId.toString());
    searchParams.set(`pagination_page_size`, size.toString());
    searchParams.set(`pagination_start_page`, page.toString());

    const data = await useBadgerFetch<UseTasksResponseObj>({
        url: `${newUrl}?${searchParams}`,
        method: 'get',
        withCredentials: true
    })();
    return data;
}

export const useTasksForJob: QueryHookType<UseTasksForJobParamsType, PagedResponse<ApiTask>> = ({
    user_id,
    page,
    size,
    jobId,
    jobType
}) => {
    return useQuery(['tasks', user_id, page, size, jobId, jobType], async () => {
        if ((jobType && jobType === 'AnnotationJob') || jobType === 'ExtractionWithAnnotationJob') {
            const data = await fetchTasksForJob(user_id, jobId, size, page);

            return {
                data: data.annotation_tasks,
                pagination: {
                    total: data.total_objects,
                    page_size: data.page_size,
                    page_num: data.current_page
                }
            };
        }
        return {
            data: [],
            pagination: {
                total: 0,
                page_size: 1,
                page_num: 15
            }
        };
    });
};

export const createNewTask = async (task: TaskModel): Promise<Task> => {
    return await useBadgerFetch<Task>({
        url: `${namespace}/tasks`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(task));
};
export const useCreateNewTaskMutation: MutationHookType<TaskModel, Task> = () => {
    const queryClient = useQueryClient();

    return useMutation(createNewTask, {
        onSuccess: () => {
            queryClient.invalidateQueries('tasks');
        }
    });
};

type UseTaskForValidatedPagesParams = {
    taskId: number | undefined;
    taskType: boolean | undefined;
};

export const useGetValidatedPages: QueryHookType<UseTaskForValidatedPagesParams, ValidationPages> =
    ({ taskId, taskType }) =>
        useQuery(['tasksPages', taskId, taskType], () => {
            if (taskType) {
                return useBadgerFetch({
                    url: `${namespace}/tasks/${taskId}/pages_summary`,
                    method: 'get'
                })();
            }
        });

interface TaskOptions {
    taskId: number;
    options?: {
        option_invalid?: string | null;
        option_edited?: string | null;
    };
}

const finishTask = async ({ taskId, options }: TaskOptions): Promise<TaskModel> => {
    const body = options
        ? {
              annotation_user_for_failed_pages: options.option_invalid || null,
              validation_user_for_reannotated_pages: options.option_edited || null
          }
        : {};
    return await useBadgerFetch<TaskModel>({
        url: `${namespace}/tasks/${taskId}/finish`,
        method: 'post'
    })(JSON.stringify(body));
};

export const useSetTaskFinishedMutation: MutationHookType<TaskOptions, TaskModel> = () => {
    const queryClient = useQueryClient();

    return useMutation(finishTask, {
        onSuccess: () => {
            queryClient.invalidateQueries('tasks');
        }
    });
};

type TaskEvent = {
    id: number;
    eventType: 'opened' | 'closed';
};

export const useSetTaskState = (taskState: TaskEvent) => {
    const body = { event_type: taskState.eventType };

    return useBadgerFetch<Task>({
        url: `${namespace}/tasks/${taskState.id}/stats`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
};

type TaskReportRequestParams = {
    userIds: string[];
    from: string;
    to: string;
};

export const useDownloadTaskReport = async (params: TaskReportRequestParams) => {
    const body = { user_ids: params.userIds, date_from: params.from, date_to: params.to };

    const response = await useBadgerFetch<Blob>({
        url: `${namespace}/tasks/export`,
        method: 'post',
        withCredentials: true,
        isBlob: true
    })(JSON.stringify(body));

    return response;
};

export const useNextTask: QueryHookType<string, { next: string }> = (taskId) =>
    useQuery(['nextTask'], async () => {
        return useBadgerFetch<{ next: string }>({
            url: `${namespace}/tasks/${taskId}/next`,
            method: 'get',
            withCredentials: true
        })();
    });
