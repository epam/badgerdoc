import { LazyDataSourceApiRequest } from '@epam/uui';
import { PagingCache, PagingFetcher } from 'api/typings';
import React, { useCallback } from 'react';
import { pageSizes } from 'shared';

export function createPagingCachedLoader<TItem, TId>(
    cache: React.MutableRefObject<PagingCache<TItem>>,
    fetcher: PagingFetcher<TItem>
) {
    return useCallback(
        async (request: LazyDataSourceApiRequest<TItem, TId, unknown>) => {
            const { range, search = '' } = request;
            const requestFrom = range?.from || 0;
            const requestCount = range?.count || 0;
            if (search !== cache.current.search) {
                const response = await fetcher(1, pageSizes._100, search);
                cache.current = { page: 1, cache: response.data, search };
                return { items: response.data };
            } else {
                const nextPage = Math.floor((requestFrom + requestCount) / pageSizes._100) + 1;
                if (nextPage !== cache.current.page) {
                    const response = await fetcher(nextPage, pageSizes._100);
                    cache.current = { page: nextPage, cache: response.data, search };
                    return { items: response.data };
                }
                return { items: cache.current.cache.slice(requestFrom, requestCount) };
            }
        },
        [cache.current]
    );
}
