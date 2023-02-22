import {
    PagedResponse,
    SortingDirection,
    SearchBody,
    QueryHookType,
    Filter,
    Operators,
    MutationHookType,
    ValidationType
} from 'api/typings';
import { Job, JobMode, JobType } from 'api/typings/jobs';
import { useQueryClient, useMutation, useQuery } from 'react-query';

import { pageSizes } from 'shared/primitives';
import { useBadgerFetch } from './api';

type UseJobsParamsType = {
    page?: number;
    size?: number;
    searchText?: string;
    sortConfig?: {
        field: keyof Job;
        direction: SortingDirection;
    };
    filters?: Array<Filter<keyof Job>>;
};

type CategoryWithTaxonomy = {
    category_id: string;
    taxonomy_id: string;
    taxonomy_version: number;
};

type JobVariablesCategory = string | number | CategoryWithTaxonomy;

export type JobVariablesWithId = JobVariables & {
    id: number;
};

export type JobVariables = {
    name: string | undefined;
    files?: string[] | number[];
    datasets?: string[];
    pipeline_name?: string | undefined;
    pipeline_version?: number;
    type: JobType;
    is_draft: boolean;
    is_auto_distribution?: boolean;
    start_manual_job_automatically?: boolean;
    categories?: JobVariablesCategory[] | undefined;
    deadline?: string;
    validation_type?: ValidationType;
    annotators?: string[];
    validators?: string[];
    owners?: string[];
    extensive_coverage?: number;
};

export type EditJobVariables = Omit<JobVariables, 'files' | 'datasets'>;

const namespace = process.env.REACT_APP_JOBMANAGER_API_NAMESPACE;
export const useJobs: QueryHookType<UseJobsParamsType, PagedResponse<Job>> = (
    { page, size, searchText, sortConfig, filters },
    options
) => {
    return useQuery(
        ['jobs', page, size, searchText, sortConfig, filters],
        async () => jobsFetcher(page, size, searchText, sortConfig, filters),
        options
    );
};
export function jobsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Job;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    filters: Filter<keyof Job>[] = []
): Promise<PagedResponse<Job>> {
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Job> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };

    return useBadgerFetch<PagedResponse<Job>>({
        url: `${namespace}/jobs/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export function jobPropFetcher(
    propName: keyof Job,
    page = 1,
    size = pageSizes._15,
    keyword: string = ''
): Promise<PagedResponse<string>> {
    const sortConfig = {
        field: propName,
        direction: SortingDirection.ASC
    };
    const filters: Filter<keyof Job>[] = [];
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
    const body: SearchBody<Job> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field as keyof Job }]
    };

    return useBadgerFetch<PagedResponse<string>>({
        url: `${namespace}/jobs/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}
type JobProgressResult = {
    [id: number]: {
        finished: number;
        total: number;
        mode: JobMode;
    };
};
export function jobProgressFetcher({ jobId }: JobByIdParams): Promise<JobProgressResult> {
    return useBadgerFetch<JobProgressResult>({
        url: `${namespace}/jobs/progress`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify([jobId]));
}

export const useJobProgress: QueryHookType<JobByIdParams, JobProgressResult> = (
    { jobId },
    options
) => {
    return useQuery(['jobProgress', jobId], async () => jobProgressFetcher({ jobId }), options);
};

export function addJob(data: JobVariables): Promise<Job> {
    return useBadgerFetch<Job>({
        url: `${namespace}/jobs/create_job`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(data));
}

export const useAddJobMutation: MutationHookType<JobVariables, Job> = () => {
    const queryClient = useQueryClient();

    return useMutation(addJob, {
        onSuccess: () => {
            queryClient.invalidateQueries('jobs');
        }
    });
};

type JobByIdParams = {
    jobId?: number;
};
export const useJobById: QueryHookType<JobByIdParams, Job | undefined> = ({ jobId }, options) => {
    return useQuery(
        ['jobDetailed', jobId],
        async () =>
            jobId
                ? useBadgerFetch<Job>({
                      url: `${namespace}/jobs/${jobId}`,
                      method: 'get',
                      withCredentials: true
                  })()
                : undefined,
        options
    );
};
type EditJobParams = { id: number; data: EditJobVariables };

export function editJob({ id, data }: EditJobParams): Promise<Job> {
    return useBadgerFetch<Job>({
        url: `${namespace}/jobs/${id}`,
        method: 'put',
        withCredentials: true
    })(JSON.stringify(data));
}

export const useEditJobMutation: MutationHookType<EditJobParams, Job> = () => {
    const queryClient = useQueryClient();

    return useMutation(editJob, {
        onSuccess: () => {
            queryClient.invalidateQueries('jobs');
        }
    });
};
