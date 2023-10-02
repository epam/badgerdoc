// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks, @typescript-eslint/no-unused-expressions */
import {
    Category,
    CreateCategory,
    FilterWithDocumentExtraOption,
    HTTPRequestMethod,
    MutationHookType,
    Operators,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    QueryInfiniteHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    UpdateCategory
} from 'api/typings';
import { InfiniteData, useQuery, useMutation, useQueryClient, useInfiniteQuery } from 'react-query';
import { pageSizes } from 'shared';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;

interface CategoriesByJobParams extends QueryHookParamsType<Category> {
    jobId?: number | undefined;
}

export const useCategories: QueryHookType<
    QueryHookParamsType<Category>,
    PagedResponse<Category>
> = ({ page, size, searchText, filters, sortConfig }, options) => {
    return useQuery(
        ['categories', page, size, searchText, filters, sortConfig],
        () => categoriesFetcher(page, size, searchText, filters, sortConfig),
        options
    );
};

export const useAddCategoriesMutation: MutationHookType<CreateCategory, any> = () => {
    const queryClient = useQueryClient();

    return useMutation(addCategories, {
        onSuccess: () => {
            queryClient.invalidateQueries('categories');
        }
    });
};

export const addCategories = async (data: CreateCategory): Promise<Category> => {
    return useBadgerFetch<Category>({
        url: `${namespace}/categories`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(data));
};

export const useUpdateCategoriesMutation: MutationHookType<UpdateCategory, any> = () => {
    const queryClient = useQueryClient();

    return useMutation(updateCategories, {
        onSuccess: () => {
            queryClient.invalidateQueries('categories');
        }
    });
};

export const updateCategories = async (data: UpdateCategory): Promise<Category> => {
    return useBadgerFetch<Category>({
        url: `${namespace}/categories/${data.id}`,
        method: 'put',
        withCredentials: true
    })(JSON.stringify(data));
};

export const getCategories = (id: string): Promise<Category> => {
    return useBadgerFetch<Category>({
        url: `${namespace}/categories/${id}`,
        method: 'get',
        withCredentials: true
    })();
};

export const useCategoriesByJob: QueryInfiniteHookType<
    Omit<CategoriesByJobParams, 'page'>,
    Category
> = ({ jobId, size, searchText, filters, sortConfig }, { enabled }) => {
    return useInfiniteQuery(
        ['categoriesByJob', jobId, size, searchText, filters, sortConfig],
        ({ pageParam = 1 }) =>
            categoriesByJobFetcher(jobId, pageParam, size, searchText, filters, sortConfig),
        {
            enabled,
            select: (data) => ({
                pages: data.pages.flat(),
                pageParams: data.pageParams
            }),
            getNextPageParam: (lastPage, pages) => (lastPage.length ? pages.length + 1 : undefined)
        }
    );
};
async function categoriesByJobFetcher(
    jobId?: number | undefined,
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    filters?: FilterWithDocumentExtraOption<keyof Category | string>[],
    sortConfig: Sorting<keyof Category> = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<Category[]> {
    const filtersArr: FilterWithDocumentExtraOption<keyof Category | string>[] = filters
        ? [...filters]
        : [];

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
    const { data } = await fetchCategories(
        `${namespace}/jobs/${jobId}/categories/search`,
        'post',
        body
    );

    return data;
}

export async function categoriesFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    filters?: FilterWithDocumentExtraOption<keyof Category | string>[],
    sortConfig: Sorting<keyof Category> = {
        field: 'name',
        direction: SortingDirection.ASC
    }
): Promise<PagedResponse<Category>> {
    const filtersArr: FilterWithDocumentExtraOption<keyof Category | string>[] = filters
        ? [...filters]
        : [];
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
    return fetchCategories(`${namespace}/categories/search`, 'post', body);
}

export async function fetchCategories(
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

// @ts-ignore
export const useAutomaticJobCategories: QueryInfiniteHookType<
    Set<string>,
    InfiniteData<PagedResponse<Category>>
> = (categories, options) => {
    return useQuery(
        ['automaticJobCategories', ...Array.from(categories.values())],
        async (pageParam) =>
            // @ts-ignore
            categoriesInfiniteFetcher({
                pageParam: pageParam.pageParam ?? categories.values().next().value
            }),
        {
            ...options,
            getNextPageParam: () => {
                categories.values().next().value || false;
            }
        }
    );
};

type categoriesInfiniteFetcherParamsType = {
    pageParam: string;
    queryKey: string[];
};

export async function categoriesInfiniteFetcher({
    pageParam
}: categoriesInfiniteFetcherParamsType): Promise<InfiniteData<PagedResponse<Category>>> {
    const body: SearchBody<Category> = {
        pagination: { page_num: 1, page_size: 15 },
        filters: [
            {
                field: 'name',
                operator: Operators.EQ,
                value: pageParam
            }
        ],
        sorting: [{ direction: SortingDirection.ASC, field: 'id' }]
    };
    return fetchInfiniteCategories(`${namespace}/categories/search`, 'post', body);
}

export async function fetchInfiniteCategories(
    url: string,
    method: HTTPRequestMethod,
    body?: SearchBody<Category>
): Promise<InfiniteData<PagedResponse<Category>>> {
    return useBadgerFetch<InfiniteData<PagedResponse<Category>>>({
        url,
        method,
        withCredentials: true
    })(JSON.stringify(body));
}

export type DocumentCategoriesByJobResponse = {
    data?: PagedResponse<Category>;
    isLoading: boolean;
    isError: boolean;
};
