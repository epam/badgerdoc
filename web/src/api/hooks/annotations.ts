// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import { CategoryDataAttrType, MutationHookType, PageInfo, QueryHookType } from 'api/typings';
import { Task } from 'api/typings/tasks';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { useBadgerFetch } from './api';
import { JobStatus } from '../typings/jobs';
import { LatestRevisionResponse } from '../../connectors/task-annotator-connector/revisionTypes';

type LatestAnnotationsParams = {
    jobId?: number;
    fileId?: number;
    revisionId?: string;
    pageNumbers?: number[];
    userId?: string;
};

type LatestAnnotationsParamsByUser = LatestAnnotationsParams & {
    userId?: string;
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

export type DocumentLink = {
    to: number;
    category: string;
    type: 'directional' | 'undirectional' | 'omnidirectional';
};

export type DocumentLinkWithName = DocumentLink & {
    documentName: string;
};

export type AnnotationsResponse = {
    revision: string;
    pages: PageInfo[];
    validated: number[];
    failed_validation_pages: number[];
    categories: string[];
    links_json: DocumentLink[];
    data?: { dataAttributes: CategoryDataAttrType[] };
};

export type AnnotationsByUser = PageInfo & {
    categories: string[];
    revision: string;
    user_id: string;
    data?: { dataAttributes: CategoryDataAttrType[] };
};

export const useLatestAnnotations: QueryHookType<LatestAnnotationsParams, AnnotationsResponse> = (
    { jobId, fileId, revisionId, pageNumbers, userId },
    options
) => {
    return useQuery(
        ['latestAnnotations', jobId, fileId, revisionId, pageNumbers, userId],
        async () => fetchLatestAnnotations(jobId, fileId, revisionId, pageNumbers, userId),
        options
    );
};

export const useLatestAnnotationsFetcher = () => {
    const queryClient = useQueryClient();

    return ({ jobId, fileId, revisionId, pageNumbers, userId }: LatestAnnotationsParams) =>
        queryClient.fetchQuery(
            ['latestAnnotations', jobId, fileId, revisionId, pageNumbers, userId],
            async () => fetchLatestAnnotations(jobId, fileId, revisionId, pageNumbers, userId)
        );
};

export const useLatestAnnotationsByUser: QueryHookType<
    LatestAnnotationsParamsByUser,
    LatestRevisionResponse
> = ({ jobId, fileId, pageNumbers, userId }, options) => {
    return useQuery(
        ['latestAnnotationsByUser', jobId, fileId, pageNumbers, userId],
        async () => fetchLatestAnnotationsByUser(jobId, fileId, pageNumbers, userId),
        options
    );
};

async function fetchLatestAnnotations(
    jobId?: number,
    fileId?: number,
    revisionId?: string,
    pageNumbers?: number[],
    userId?: string
): Promise<AnnotationsResponse> {
    const pageNums = pageNumbers?.map((pageNumber) => `page_numbers=${pageNumber}`);
    const revId = revisionId || 'latest';
    const user = userId ? `&user_id=${userId}` : '';
    return useBadgerFetch<AnnotationsResponse>({
        url: `${namespace}/annotation/${jobId}/${fileId}/${revId}?${pageNums?.join('&')}${user}`,
        method: 'get',
        withCredentials: true
    })();
}

async function fetchLatestAnnotationsByUser(
    jobId?: number,
    fileId?: number,
    pageNumbers?: number[],
    userId?: string
): Promise<any> {
    if (!jobId || !fileId) {
        return undefined;
    }
    const pageNums = pageNumbers?.map((pageNumber) => `page_numbers=${pageNumber}`);
    const userQueryStr = userId ? `&user_id=${userId}` : '';
    return useBadgerFetch({
        url: `${namespace}/annotation/${jobId}/${fileId}/latest_by_user?${pageNums?.join(
            '&'
        )}${userQueryStr}`,
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
    selectedLabelsId?: string[];
    links?: DocumentLink[];
};

const addAnnotations = async (data: addAnnotationsParams) => {
    const body = {
        user: data.userId,
        pages: data.pages,
        base_revision: data.revision,
        validated: data.validPages,
        failed_validation_pages: data.invalidPages,
        categories: data.selectedLabelsId,
        links_json: data.links
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
