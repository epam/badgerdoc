// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo, useRef } from 'react';
import { useLazyDataSource } from '@epam/uui';
import { FilterWithDocumentExtraOption, PagedResponse, PagingCache } from 'api/typings';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';

export const useEntity = <TItem, TId>(
    fetcher: (...args: Array<any>) => Promise<PagedResponse<TItem>>,
    filters?: FilterWithDocumentExtraOption<keyof TItem>[]
) => {
    const cache = useRef<PagingCache<TItem>>({
        page: -1,
        search: '',
        cache: []
    });

    const api = createPagingCachedLoader<TItem, TId>(
        cache,
        async (pageNumber, pageSize, keyword) =>
            await fetcher(pageNumber, pageSize, keyword, filters)
    );

    const dataSource = useLazyDataSource({ api }, []);

    return useMemo(() => ({ dataSource, cache }), []);
};
