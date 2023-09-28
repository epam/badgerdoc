// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import {
    MutationHookType,
    Operators,
    PagedResponse,
    Pipeline,
    QueryHookType,
    SearchBody,
    SortingDirection,
    FilterWithDocumentExtraOption
} from 'api/typings';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { useBadgerFetch } from './api';
import { pageSizes } from '../../shared';

const namespace = process.env.REACT_APP_PIPELINES_API_NAMESPACE;

type UsePipelineParamsType = {
    page?: number;
    size?: number;
    searchText?: string;
    sortConfig?: {
        field: keyof Pipeline;
        direction: SortingDirection;
    };
    filters?: Array<FilterWithDocumentExtraOption<keyof Pipeline>>;
};

export const usePipelines: QueryHookType<UsePipelineParamsType, PagedResponse<Pipeline>> = (
    { page, size, sortConfig, searchText, filters },
    options
) => {
    return useQuery(
        ['pipelines', page, size, searchText, sortConfig, filters],
        () => pipelinesFetcher(page, size, searchText, sortConfig, filters),
        options
    );
};

export function pipelinesFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Pipeline;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    filters: FilterWithDocumentExtraOption<keyof Pipeline>[] = []
): Promise<PagedResponse<Pipeline>> {
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Pipeline> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return useBadgerFetch<PagedResponse<Pipeline>>({
        url: `${namespace}/pipelines/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

type PipelineByNameParams = {
    pipelineName?: string;
    version?: number;
};
export const usePipelineByName: QueryHookType<PipelineByNameParams, Pipeline> = (
    { pipelineName, version },
    options
) => {
    return useQuery(
        ['pipeline', pipelineName, version],
        () =>
            useBadgerFetch<Pipeline>({
                url: `${namespace}/pipeline?name=${pipelineName}${
                    version ? `&version=${version}` : ''
                }`,
                method: 'get',
                withCredentials: true
            })(),
        options
    );
};

export function addPipeline(pipeline: Partial<Pipeline>): Promise<Pick<Pipeline, 'id'>> {
    return useBadgerFetch<Pick<Pipeline, 'id'>>({
        url: `${namespace}/pipeline`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(pipeline));
}

export const useAddPipelineMutation: MutationHookType<
    Partial<Pipeline>,
    Pick<Pipeline, 'id'>
> = () => {
    const queryClient = useQueryClient();

    return useMutation(addPipeline, {
        onSuccess: () => {
            queryClient.invalidateQueries('datasets');
        }
    });
};

// export const usePipelinesDataSource = () => {
//     const { data: basePipelines } = usePipelines(
//         {
//             page: 1,
//             size: 100,
//             searchText: '',
//             sortConfig: { field: 'name', direction: SortingDirection.ASC }
//         },
//         {}
//     );
//     return useArrayDataSource(
//         {
//             items: basePipelines?.data ?? []
//         },
//         [basePipelines]
//     );
// };
