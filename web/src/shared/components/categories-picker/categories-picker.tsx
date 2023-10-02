// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { FC, useCallback, useRef } from 'react';
import { JobValues } from '../../../connectors/edit-job-connector/edit-job-connector';
import { Category, PagingCache, PagingFetcher, SortingDirection } from '../../../api/typings';
import { InfoIcon } from '../info-icon/info-icon';
import { ModelValues } from '../../../components/model/model.models';
import { categoriesFetcher } from '../../../api/hooks/categories';
import { pageSizes } from '../../primitives/page-sizes';

import { ILens, LazyDataSourceApiRequest, useLazyDataSource } from '@epam/uui';
import { LabeledInput, PickerInput } from '@epam/loveship';

type CategoriesPickerProps = {
    lens: ILens<JobValues | ModelValues>;
    categories?: Category[];
};

const CategoriesPicker: FC<CategoriesPickerProps> = ({ lens }) => {
    const CategoriesCache = useRef<PagingCache<Category>>({
        page: -1,
        cache: [],
        search: ''
    });

    function createCategoriesPagingCachedLoader<TItem, TId>(
        cache: React.MutableRefObject<PagingCache<TItem>>,
        fetcher: PagingFetcher<TItem>
    ) {
        return useCallback(
            async (request: LazyDataSourceApiRequest<TItem, TId, unknown>) => {
                const { range, search = '' } = request;
                const requestFrom = range?.from || 0;
                const requestCount = range?.count || 0;
                if (search !== cache.current.search) {
                    const response = await fetcher(1, pageSizes._100, search, [], {
                        field: 'name',
                        direction: SortingDirection.ASC
                    });
                    cache.current = { page: 1, cache: response.data, search };
                    return { items: response.data };
                } else {
                    const nextPage = Math.floor((requestFrom + requestCount) / pageSizes._100) + 1;
                    if (nextPage !== cache.current.page) {
                        const response = await fetcher(nextPage, pageSizes._100, search, [], {
                            field: 'name',
                            direction: SortingDirection.ASC
                        });
                        cache.current = { page: nextPage, cache: response.data, search };
                        return { items: response.data };
                    }
                    return { items: cache.current.cache.slice(requestFrom, requestCount) };
                }
            },
            [cache.current]
        );
    }

    const loadCategories = createCategoriesPagingCachedLoader<Category, Category>(
        CategoriesCache,
        async (pageNumber, pageSize, searchText, filters) =>
            await categoriesFetcher(pageNumber, pageSize, searchText, filters)
    );

    const categoriesDataSource = useLazyDataSource({ api: loadCategories }, []);

    return (
        <LabeledInput cx={`m-t-15`} label="Categories" {...lens.prop('categories').toProps()}>
            <div className="flex align-vert-center">
                <PickerInput
                    {...lens.prop('categories').toProps()}
                    dataSource={categoriesDataSource}
                    getName={(item) => item?.name ?? ''}
                    entityName="Categories name"
                    selectionMode="multi"
                    valueType={'entity'}
                    sorting={{ field: 'name', direction: 'asc' }}
                    placeholder="Select categories"
                />
                <InfoIcon
                    title="Select Categories"
                    description="Categories of text available for annotation to users."
                />
            </div>
        </LabeledInput>
    );
};

export default CategoriesPicker;
