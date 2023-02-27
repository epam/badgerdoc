import {
    HTTPRequestMethod,
    MutationHookType,
    Operators,
    PagedResponse,
    QueryHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    Basement,
    FilterWithDocumentExtraOption
} from 'api/typings';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { pageSizes } from 'shared';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_MODELS_API_NAMESPACE;

type UseBasementsParamsType = {
    page: number;
    size: number;
    searchText: string;
    userId?: string | null;
    sortConfig: Sorting<keyof Basement>;
    filters?: Array<FilterWithDocumentExtraOption<keyof Basement>>;
};

export const useBasements: QueryHookType<UseBasementsParamsType, PagedResponse<Basement>> = (
    { page, size, searchText, sortConfig },
    options
) => {
    return useQuery(
        ['basements', page, size, searchText, sortConfig],
        () => basementsFetcher(page, size, searchText, sortConfig),
        options
    );
};

export function addBasement(data: Basement): Promise<Basement> {
    return useBadgerFetch<Basement>({
        url: `${namespace}/basements/create`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(data));
}

export const useAddBasementMutation: MutationHookType<Basement, Basement> = () => {
    const queryClient = useQueryClient();

    return useMutation(addBasement, {
        onSuccess: () => {
            queryClient.invalidateQueries('basements');
        }
    });
};

export async function basementsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: Sorting<keyof Basement> = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<Basement>> {
    const filters: FilterWithDocumentExtraOption<keyof Basement>[] = [];
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Basement> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return fetchBasements(`${namespace}/basements/search`, 'post', body);
}

export async function fetchBasements(
    url: string,
    method: HTTPRequestMethod,
    body?: SearchBody<Basement>
): Promise<PagedResponse<Basement>> {
    return useBadgerFetch<PagedResponse<Basement>>({
        url,
        method,
        withCredentials: true
    })(JSON.stringify(body));
}
