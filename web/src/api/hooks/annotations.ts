import { MutationHookType, PageInfo, QueryHookType } from 'api/typings';
import { Task } from 'api/typings/tasks';
import { useMutation, useQuery } from 'react-query';
import { useBadgerFetch } from './api';
import { JobStatus } from '../typings/jobs';

type LatestAnnotationsParams = {
    jobId?: number;
    fileId?: number;
    revisionId?: string;
    pageNumbers?: number[];
};
const namespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;

export type FileJobs = {
    fileId: FileId;
};

export type FileId = {
    id: number;
    name: string;
    status: JobStatus;
};

export function fileJobsFetcher(fileIds: number[]): Promise<FileJobs[]> {
    return useBadgerFetch<FileJobs[]>({
        url:
            `${namespace}/jobs?` +
            fileIds
                .filter((item, index, array) => array.indexOf(item) === index)
                .map((e) => `file_ids=${e}`)
                .join('&'),
        method: 'get',
        withCredentials: true
    })();
}

export type AnotationsResponse = {
    revision: string;
    pages: PageInfo[];
    validated: number[];
    failed_validation_pages: number[];
};
export const useLatestAnnotations: QueryHookType<LatestAnnotationsParams, AnotationsResponse> = (
    { jobId, fileId, revisionId, pageNumbers },
    options
) => {
    return useQuery(
        ['latestAnnotations', jobId, fileId, revisionId, pageNumbers],
        async () => fetchLatestAnnotations(jobId, fileId, revisionId, pageNumbers),
        options
    );
};

async function fetchLatestAnnotations(
    jobId?: number,
    fileId?: number,
    revisionId?: string,
    pageNumbers?: number[]
): Promise<any> {
    const pageNums = pageNumbers?.map((pageNumber) => `page_numbers=${pageNumber}`);
    const revId = revisionId || 'latest';
    return useBadgerFetch({
        url: `${namespace}/annotation/${jobId}/${fileId}/${revId}?${pageNums?.join('&')}`,
        method: 'get',
        withCredentials: true
    })();
}

type addAnnotationsParams = {
    taskId: number;
    pages: PageInfo[];
    userId?: string;
    revision?: string;
    validPages: number[];
    invalidPages: number[];
};

export const addAnnotations = async (data: addAnnotationsParams) => {
    const body = {
        user: data.userId,
        pages: data.pages,
        base_revision: data.revision,
        validated: data.validPages,
        failed_validation_pages: data.invalidPages
    };
    return useBadgerFetch({
        url: `${namespace}/annotation/${data.taskId}`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
};

export const useAddAnnotationsMutation: MutationHookType<addAnnotationsParams, any> = () => {
    return useMutation(addAnnotations);
};

type startJobParams = {
    jobId: number;
};
export const useStartJobMutation: MutationHookType<startJobParams, any> = () => {
    return useMutation(startJob);
};

export async function startJob({ jobId }: startJobParams): Promise<Task[]> {
    return useBadgerFetch<Task[]>({
        url: `${namespace}/jobs/${jobId}/start`,
        method: 'post',
        withCredentials: true
    })();
}
