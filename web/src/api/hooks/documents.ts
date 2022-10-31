import { useMutation, useQuery, useQueryClient } from 'react-query';
import {
    FileDocument,
    Filter,
    MutationHookType,
    Operators,
    PagedResponse,
    SearchBody,
    SortingDirection
} from 'api/typings';

import { pageSizes } from 'shared/primitives';
import { QueryHookType } from '../typings';
import { UploadFilesReponse } from 'api/typings/files';
import { useBadgerFetch } from './api';
import { FileInfo } from 'api/typings/bonds';

const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

type UseDocumentsParamsType = {
    page?: number;
    size?: number;
    filters?: Filter<keyof FileDocument>[];
    searchText?: string;
    sortConfig?: {
        field: keyof FileDocument;
        direction: SortingDirection;
    };
};

export const useDocuments: QueryHookType<UseDocumentsParamsType, PagedResponse<FileDocument>> = (
    { page, size, filters, searchText, sortConfig },
    options
) => {
    return useQuery(
        ['documents', page, size, searchText, sortConfig, filters],
        async () => documentsFetcher(page, size, searchText, filters, sortConfig),
        options
    );
};

export function documentsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText: string = '',
    filters: Filter<keyof FileDocument>[] = [],
    sortConfig: {
        field: keyof FileDocument;
        direction: SortingDirection;
    } = {
        field: 'original_name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<FileDocument>> {
    const searchFilter: Filter<keyof FileDocument> = {
        field: 'original_name',
        operator: Operators.ILIKE,
        value: `%${searchText.trim().toLowerCase()}%`
    };
    const body: SearchBody<FileDocument> = {
        pagination: { page_num: page, page_size: size },
        filters: [searchFilter, ...filters] ?? [],
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return useBadgerFetch<PagedResponse<FileDocument>>({
        url: `${namespace}/files/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

const uploadFiles = async (files: Array<File>): Promise<UploadFilesReponse> => {
    const formData = new FormData();
    files.forEach((file) => {
        formData.append('files', file, file.name);
    });
    return useBadgerFetch<UploadFilesReponse>({
        url: `${namespace}/files`,
        method: 'post',
        plainHeaders: true,
        withCredentials: true
    })(formData);
};

export const useUploadFilesMutation: MutationHookType<File[], FileInfo[]> = () => {
    const queryClient = useQueryClient();
    return useMutation(uploadFiles, {
        onSuccess: () => {
            queryClient.invalidateQueries('documents');
        }
    });
};

export const useDocumentsInJob: QueryHookType<
    UseDocumentsParamsType & { filesIds: Array<number> },
    PagedResponse<FileDocument>
> = ({ page, size, filters = [], filesIds, searchText = '' }, options) => {
    const extendedFilters: typeof filters = [
        ...filters,
        { field: 'id', operator: Operators.IN, value: filesIds }
    ];
    return useQuery(
        ['documents', page, size, filters, filesIds, searchText],
        async () => documentsFetcher(page, size, searchText, extendedFilters),
        { ...options, ...{ enabled: !!filesIds.length, keepPreviousData: true } }
    );
};
