import {
    FileDocument,
    FilterWithDocumentExtraOption,
    Operators,
    PagedResponse,
    QueryHookType,
    SearchBody,
    SortingDirection
} from '../typings';
import { useQuery } from 'react-query';
import { DocumentJob } from '../typings/jobs';
import { DocumentJobRevisionsResponse } from '../typings/revisions';
import { pageSizes } from '../../shared';
import { useBadgerFetch } from './api';

const jobManagerNamespace = process.env.REACT_APP_JOBMANAGER_API_NAMESPACE;
const annotationManagerNamespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;
const filesNamespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

export async function documentJobsFetcher(
    page: number = 1,
    size = pageSizes._15,
    search: string = '',
    filterById: FilterWithDocumentExtraOption<keyof DocumentJob>[] = []
): Promise<PagedResponse<DocumentJob>> {
    const filters: FilterWithDocumentExtraOption<keyof DocumentJob>[] = [...filterById];
    if (search) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${search.trim().toLowerCase()}%`
        });
    }
    const body = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: SortingDirection.ASC, field: 'name' }]
    };

    return useBadgerFetch<PagedResponse<DocumentJob>>({
        url: `${jobManagerNamespace}/jobs/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export type useDocumentJobsRevisionsParamsType = {
    documentId: string | number;
    jobId: number;
};

export const useDocumentJobsRevisions: QueryHookType<
    useDocumentJobsRevisionsParamsType,
    DocumentJobRevisionsResponse
> = ({ documentId, jobId }, options) => {
    return useQuery(
        ['document', 'revisions', documentId, jobId],
        async () => documentJobsRevisionsFetcher(Number(documentId), jobId),
        options
    );
};

export async function documentJobsRevisionsFetcher(
    documentId: number,
    jobId: number
): Promise<DocumentJobRevisionsResponse> {
    return useBadgerFetch({
        url: `${annotationManagerNamespace}/revisions/${jobId}/${documentId}`,
        method: 'get',
        withCredentials: true
    })() as Promise<DocumentJobRevisionsResponse>;
}

export function documentNamesFetcher(
    pageNumber = 1,
    pageSize = pageSizes._100,
    filters: FilterWithDocumentExtraOption<keyof FileDocument>[],
    keyword: string = ''
): Promise<PagedResponse<string>> {
    const nameFieldName = 'original_name';
    const sortConfig = {
        field: nameFieldName,
        direction: SortingDirection.ASC
    };
    const extraFilters: FilterWithDocumentExtraOption<keyof FileDocument>[] = [];
    extraFilters.push({
        field: nameFieldName,
        operator: Operators.DISTINCT
    });
    if (keyword) {
        extraFilters.push({
            field: nameFieldName,
            operator: Operators.ILIKE,
            value: `%${keyword}%`
        });
    }
    const body: SearchBody<FileDocument> = {
        pagination: { page_num: pageNumber, page_size: pageSize },
        filters: [...extraFilters, ...filters],
        sorting: [
            { direction: sortConfig.direction, field: sortConfig.field as keyof FileDocument }
        ]
    };

    return useBadgerFetch<PagedResponse<string>>({
        url: `${filesNamespace}/files/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}
