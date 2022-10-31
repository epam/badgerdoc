import {
    User,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    Filter,
    Operators
} from 'api/typings';
import { useQuery } from 'react-query';
import { pageSizes } from 'shared';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_USERS_API_NAMESPACE;

export const useUsers: QueryHookType<QueryHookParamsType<User>, PagedResponse<User>> = (
    { page, size },
    options
) => {
    return useQuery(['users', page, size], () => usersFetcher(page, size), options);
};

export async function usersFetcher(
    page = 1,
    size = pageSizes._15,
    search: string = '',
    filters: Array<Filter<keyof User>> = []
): Promise<PagedResponse<User>> {
    const body = {
        filters: [...filters]
    };
    if (search) {
        // name is not in the model
        body.filters.push({ field: 'name', operator: Operators.LIKE, value: search } as never);
    }

    const data = await useBadgerFetch<Array<User>>({
        url: `${namespace}/users/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));

    return {
        data,
        pagination: {
            has_more: false,
            min_pages_left: 1,
            page_num: page,
            page_size: size,
            total: data.length
        }
    };
}

export const useUserByForJob: QueryHookType<any, PagedResponse<User>> = ({
    page,
    size,
    filters
}) => {
    return useQuery(['user', page, size, filters], async () => {
        const body = {
            filters: filters
        };
        const data = await useBadgerFetch<Array<User>>({
            url: `${namespace}/users/search`,
            method: 'post',
            withCredentials: true
        })(JSON.stringify(body));
        return {
            data,
            pagination: {
                total: data.length
            }
        };
    });
};
