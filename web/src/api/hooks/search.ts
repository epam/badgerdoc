import { Operators, PagedResponse, QueryHookType } from 'api/typings';
import { useQuery } from 'react-query';
import {
    FacetsBody,
    UseFacetsParamsType,
    FacetsResponse,
    FacetsBodyFilters,
    Pieces,
    UsePiecesParamsType,
    FacetFilter
} from 'api/typings/search';
import { useBadgerFetch } from './api';
import { pageSizes } from 'shared';

const namespace = process.env.REACT_APP_SEARCH_API_NAMESPACE;

export const useFacets: QueryHookType<UseFacetsParamsType, FacetsResponse> = ({
    query,
    categoryLimit,
    jobLimit,
    categoryFilter,
    jobFilter
}) => {
    return useQuery(
        ['facets', query, categoryLimit, jobLimit, categoryFilter, jobFilter],
        async () => facetsFetcher(query, categoryLimit, jobLimit, categoryFilter, jobFilter)
    );
};

export const facetsFetcher = (
    query: string,
    categoryLimit: number,
    jobLimit: number,
    categoryFilter: string[],
    jobFilter: string[]
): Promise<FacetsResponse> => {
    const body: FacetsBody = {
        facets: [
            {
                name: 'category'
            },
            {
                name: 'job_id'
            }
        ]
    };
    const bodyFilters: FacetsBodyFilters[] = [];
    const IN = Operators.IN;

    if (categoryLimit) body.facets[0].limit = categoryLimit;
    if (jobLimit) body.facets[1].limit = jobLimit;
    if (query.trim.length) body.query = query;
    if (categoryFilter.length) {
        bodyFilters[bodyFilters.length] = {
            field: 'category',
            operator: IN,
            value: categoryFilter
        };
    }
    if (jobFilter.length) {
        bodyFilters[bodyFilters.length] = {
            field: 'job_id',
            operator: IN,
            value: jobFilter
        };
    }
    if (bodyFilters.length) {
        body.filters = bodyFilters;
    }

    return useBadgerFetch<FacetsResponse>({
        url: `${namespace}/facets`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
};

export const usePieces: QueryHookType<UsePiecesParamsType, PagedResponse<Pieces>> = (
    { page, size, searchText, sort, filter },
    options
) => {
    return useQuery(
        ['documents', page, size, searchText, sort, filter],
        async () => documentsFetcher(page, size, searchText, sort, filter),
        options
    );
};

export function documentsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText: string = '',
    sort: string,
    filter: FacetFilter
): Promise<PagedResponse<Pieces>> {
    let sorting: { field: string; direction: string }[] = [];
    const filters = [];
    const categoryFilter = Object.values(filter['category'])
        .map((el) => el)
        .filter((item) => item.value);
    const jobFilter = Object.values(filter['job_id'])
        .map((el) => el)
        .filter((item) => item.value);

    if (sort !== 'relevancy') {
        sorting = [
            {
                field: sort,
                direction: 'asc'
            }
        ];
    }

    if (categoryFilter.length) {
        filters.push({
            field: 'category',
            operator: Operators.IN,
            value: categoryFilter.map(({ id }) => id)
        });
    }

    if (jobFilter.length) {
        filters.push({
            field: 'job_id',
            operator: Operators.IN,
            value: jobFilter.map(({ id }) => id)
        });
    }

    const body = {
        query: searchText,
        pagination: { page_num: page, page_size: size },
        sorting,
        filters
    };

    return useBadgerFetch<PagedResponse<Pieces>>({
        url: `${namespace}/pieces`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}
