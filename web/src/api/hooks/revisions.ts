// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import {
    FilterWithDocumentExtraOption,
    Operators,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    Revision,
    SearchBody,
    SortingDirection
} from 'api/typings';
import { useQuery } from 'react-query';
import { pageSizes } from 'shared/primitives';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;

export const useRevisions: QueryHookType<QueryHookParamsType<Revision>, PagedResponse<Revision>> = (
    params,
    options
) => {
    const { searchText, sortConfig, size: pageSize, page: pageNum, filters } = params;
    return useQuery(
        ['revisions', searchText, sortConfig, pageSize, pageNum],
        () => revisionsFetcher(pageNum, pageSize, searchText, sortConfig, filters),
        options
    );
};
export function revisionsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Revision;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    filters: FilterWithDocumentExtraOption<keyof Revision>[] = []
): Promise<PagedResponse<Revision>> {
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Revision> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };
    return useBadgerFetch<PagedResponse<Revision>>({
        url: `${namespace}/annotation`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export function revisionPropFetcher(
    propName: keyof Revision,
    page = 1,
    size = pageSizes._15,
    keyword: string = ''
): Promise<PagedResponse<string>> {
    const sortConfig = {
        field: propName,
        direction: SortingDirection.ASC
    };
    const filters: FilterWithDocumentExtraOption<keyof Revision>[] = [];
    filters.push({
        field: propName,
        operator: Operators.DISTINCT
    });
    if (keyword) {
        filters.push({
            field: propName,
            operator: Operators.ILIKE,
            value: `%${keyword}%`
        });
    }
    const body: SearchBody<Revision> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field as keyof Revision }]
    };

    return useBadgerFetch<PagedResponse<string>>({
        url: `${namespace}/annotation`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}
