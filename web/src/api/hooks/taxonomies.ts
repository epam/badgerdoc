import {
    Filter,
    HTTPRequestMethod,
    Operators,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    Taxon
} from 'api/typings';
import { useQuery } from 'react-query';
import { pageSizes } from 'shared';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_TAXONOMIES_API_NAMESPACE;

export const useTaxonomies: QueryHookType<QueryHookParamsType<Taxon>, PagedResponse<Taxon>> = (
    { page, size, searchText, filters, sortConfig },
    options
) => {
    return useQuery(
        ['taxonomies', page, size, searchText, filters, sortConfig],
        () => taxonomiesFetcher(page, size, searchText, filters, sortConfig),
        options
    );
};

export async function taxonomiesFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    filters?: Filter<keyof Taxon>[],
    sortConfig: Sorting<keyof Taxon> = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<Taxon>> {
    const filtersArr: Filter<keyof Taxon>[] = filters ? [...filters] : [];
    if (searchText) {
        filtersArr.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }

    const body: SearchBody<Taxon> = {
        pagination: { page_num: page, page_size: size },
        filters: filtersArr,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return fetchTaxonomies(`${namespace}/taxons/search`, 'post', body);
}

export async function fetchTaxonomies(
    url: string,
    method: HTTPRequestMethod,
    body?: SearchBody<Taxon>
): Promise<PagedResponse<Taxon>> {
    return useBadgerFetch<PagedResponse<Taxon>>({
        url,
        method,
        withCredentials: true
    })(JSON.stringify(body));
}
