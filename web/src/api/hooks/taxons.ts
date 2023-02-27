import {
    FilterWithDocumentExtraOption,
    HTTPRequestMethod,
    Operators,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    Taxon,
    Taxonomy
} from 'api/typings';
import { useQuery } from 'react-query';
import { pageSizes } from 'shared';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_TAXONOMIES_API_NAMESPACE;

export const useTaxons: QueryHookType<QueryHookParamsType<Taxon>, PagedResponse<Taxon>> = (
    { page, size, searchText, searchField, filters, sortConfig },
    options
) => {
    return useQuery(
        ['taxons', page, size, searchText, filters, sortConfig],
        () => taxonsFetcher(page, size, searchText, filters, sortConfig, searchField),
        options
    );
};

export const useAllTaxonomies: QueryHookType<
    QueryHookParamsType<Taxonomy>,
    PagedResponse<Taxonomy>
> = ({ page, size, searchText, filters, sortConfig }, options) => {
    return useQuery(
        ['taxonomies/all', page, size, searchText, filters, sortConfig],
        () => taxonomiesFetcher(page, size, searchText, filters, sortConfig),
        options
    );
};

export async function taxonsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    filters?: FilterWithDocumentExtraOption<keyof Taxon>[],
    sortConfig: Sorting<keyof Taxon> = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    searchField: keyof Taxon | undefined = 'name'
): Promise<PagedResponse<Taxon>> {
    const filtersArr: FilterWithDocumentExtraOption<keyof Taxon>[] = filters ? [...filters] : [];
    if (searchText) {
        filtersArr.push({
            field: searchField,
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }

    const body: SearchBody<Taxon> = {
        pagination: { page_num: page, page_size: size },
        filters: filtersArr,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return fetchTaxons(`${namespace}/taxons/search`, 'post', body);
}

export async function taxonomiesFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    filters?: FilterWithDocumentExtraOption<keyof Taxonomy>[],
    sortConfig: Sorting<keyof Taxonomy> = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<Taxonomy>> {
    const filtersArr: FilterWithDocumentExtraOption<keyof Taxonomy>[] = filters ? [...filters] : [];
    if (searchText) {
        filtersArr.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }

    const body: SearchBody<Taxonomy> = {
        pagination: { page_num: page, page_size: size },
        filters: filtersArr,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return fetchTaxonomies(`${namespace}/taxonomy/all`, 'post', body);
}

export async function fetchTaxons(
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

export async function fetchTaxonomies(
    url: string,
    method: HTTPRequestMethod,
    body?: SearchBody<Taxonomy>
): Promise<PagedResponse<Taxonomy>> {
    return useBadgerFetch<PagedResponse<Taxonomy>>({
        url,
        method,
        withCredentials: true
    })(JSON.stringify(body));
}

type TaxonomyByCategoryAndJobIdParams = {
    jobId?: number;
    categoryId?: string | number;
};

type TaxonomyByJobIdParams = {
    jobId?: number;
};

export type TaxonomyByCategoryAndJobIdResponse = {
    name: string;
    id: string;
    version: number;
}[];

export type TaxonomyByJobIdResponse = {
    name: string;
    id: string;
    version: number;
    category_id: string;
}[];

export const useLinkTaxonomyByCategoryAndJobId: QueryHookType<
    TaxonomyByCategoryAndJobIdParams,
    TaxonomyByCategoryAndJobIdResponse
> = ({ jobId, categoryId }, options) => {
    return useQuery(
        ['taxonomy', jobId, categoryId],
        async () =>
            jobId && categoryId ? getLinkedTaxonomyByCategoryAndJobId(jobId, categoryId) : [],
        options
    );
};

async function getLinkedTaxonomyByCategoryAndJobId(
    jobId?: number,
    categoryId?: string | number
): Promise<any> {
    return useBadgerFetch({
        url: `${namespace}/taxonomy/link_category/${jobId}/${categoryId}`,
        method: 'get',
        withCredentials: true
    })();
}

export const useTaxonomiesByJobId: QueryHookType<TaxonomyByJobIdParams, TaxonomyByJobIdResponse> =
    ({ jobId }) => {
        return useQuery(
            ['taxonomiesByJob', jobId],
            async () => jobId && fetchTaxonomiesByJobId(jobId)
        );
    };

async function fetchTaxonomiesByJobId(jobId: number): Promise<any> {
    if (!jobId) return;
    return useBadgerFetch({
        url: `${namespace}/taxonomy?job_id=${jobId}`,
        method: 'get',
        withCredentials: true
    })();
}
