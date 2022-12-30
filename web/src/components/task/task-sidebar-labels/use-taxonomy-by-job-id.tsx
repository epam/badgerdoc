/* eslint-disable @typescript-eslint/no-unused-vars */
import { useBadgerFetch } from 'api/hooks/api';
import {
    Category,
    Filter,
    HTTPRequestMethod,
    Operators,
    PagedResponse,
    SearchBody,
    SortingDirection,
    Taxon
} from 'api/typings';

import { useQuery } from 'react-query';
import { pageSizes } from 'shared';

const namespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;

const defaultFilters: any[] = [];
const defaultSort = {
    field: 'id',
    direction: SortingDirection.ASC
};
type useTaxonomyByJobIdProps = {
    jobId: string;
    searchText?: string | null;
    pageNum?: number;
    pageSize?: number;
    filters?: any;
    sortConfig?: any;
};

export const useTaxonomyByJobId = ({
    jobId,
    searchText = null,
    pageNum = 1,
    pageSize = pageSizes._100,
    filters = defaultFilters,
    sortConfig = defaultSort
}: useTaxonomyByJobIdProps) => {
    return useQuery(['categories', pageNum, pageSize, searchText, filters, sortConfig], () =>
        categoryFetcher(pageNum, pageSize, searchText, filters, sortConfig, jobId)
    );
};

async function categoryFetcher(
    page: number,
    size: number,
    searchText: string | null,
    filters: any,
    sortConfig: { direction: any; field: any },
    jobId: string
): Promise<PagedResponse<Category>> {
    const filtersArr: Filter<keyof Taxon>[] = filters ? [...filters] : [];
    if (searchText) {
        filtersArr.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }

    const body: SearchBody<Category> = {
        pagination: { page_num: page, page_size: size },
        filters: filtersArr,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return fetchCategories(`${namespace}/jobs/${jobId}/categories/search`, 'post', body);
}

async function fetchCategories(
    url: string,
    method: HTTPRequestMethod,
    body?: SearchBody<Category>
): Promise<PagedResponse<Category>> {
    return useBadgerFetch<PagedResponse<Category>>({
        url,
        method,
        withCredentials: true
    })(JSON.stringify(body));
}
