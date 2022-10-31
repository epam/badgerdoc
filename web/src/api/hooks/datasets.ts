import {
    Dataset,
    FileDocument,
    Filter,
    MutationHookType,
    Operators,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    SearchBody,
    SortingDirection
} from 'api/typings';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { pageSizes } from 'shared/primitives';
import { DatasetWithFiles } from 'components/dataset/dataset-choose-form';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

export const useDatasets: QueryHookType<QueryHookParamsType<Dataset>, PagedResponse<Dataset>> = (
    params,
    options
) => {
    const { searchText, sortConfig, size: pageSize, page: pageNum } = params;
    return useQuery(
        ['datasets', searchText, sortConfig, pageSize, pageNum],
        () => datasetsFetcher(pageNum, pageSize, searchText, sortConfig),
        options
    );
};
export function datasetsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Dataset;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<Dataset>> {
    const filters: Filter<keyof Dataset>[] = [];
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Dataset> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return useBadgerFetch<PagedResponse<Dataset>>({
        url: `${namespace}/datasets/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export function addFilesToDataset(dataset: DatasetWithFiles): Promise<DatasetWithFiles> {
    const { name, objects } = dataset;
    return useBadgerFetch<DatasetWithFiles>({
        url: `${namespace}/datasets/bonds`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify({ name, objects }));
}

export const useAddFilesToDatasetMutation: MutationHookType<DatasetWithFiles, DatasetWithFiles> =
    () => {
        const queryClient = useQueryClient();

        return useMutation(addFilesToDataset, {
            onSuccess: () => {
                queryClient.invalidateQueries('datasets');
                queryClient.invalidateQueries('documents');
            }
        });
    };

export function addDataset(name: string): Promise<Dataset> {
    return useBadgerFetch<Dataset>({
        url: `${namespace}/datasets`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify({ name }));
}

export const useAddDatasetMutation: MutationHookType<string, Dataset> = () => {
    const queryClient = useQueryClient();

    return useMutation(addDataset, {
        onSuccess: () => {
            queryClient.invalidateQueries('datasets');
        }
    });
};

export const deleteDataset = async (name: string): Promise<FileDocument> =>
    useBadgerFetch<FileDocument>({
        url: `${namespace}/datasets`,
        method: 'delete',
        withCredentials: true
    })(JSON.stringify({ name }));

export const useDeleteDatasetMutation: MutationHookType<string, FileDocument> = () => {
    const queryClient = useQueryClient();

    return useMutation(deleteDataset, {
        onSuccess: () => {
            queryClient.invalidateQueries('datasets');
        }
    });
};
