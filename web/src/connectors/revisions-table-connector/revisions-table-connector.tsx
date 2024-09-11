// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import { DataTable } from '@epam/loveship';
import React, { FC, useEffect, useMemo, useRef, useState } from 'react';
import { useLazyDataSource } from '@epam/uui';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Revision, SortingDirection } from 'api/typings';
import { pageSizes, TableWrapper, usePageTable } from 'shared';
import { revisionsColumns } from './revisions-columns';
import {
    useColumnPickerFilter,
    useDateRangeFilter
} from '../../shared/components/filters/column-picker';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
import { datasetPropFetcher, useDatasets } from 'api/hooks/datasets';

//TODO: move out styles from the connector
import styles from './revisions-table-connector.module.scss';

type RevisionsTableConnectorProps = {
    onRowClick: (id: number) => void;
    onRevisionSelect?: (dataset: number[]) => void;
    checkedValues?: number[] | string[];
};
const size = pageSizes._100;

export const RevisionsTableConnector: FC<RevisionsTableConnectorProps> = ({
    onRowClick,
    onRevisionSelect,
    checkedValues
}) => {
    const [selectedRevisions, setSelectedRevisions] = useState<number[] | []>([]);
    const {
        pageConfig,
        onPageChange,
        totalCount,
        onTotalCountChange,
        searchText,
        tableValue,
        onTableValueChange,
        sortConfig,
        setSortConfig,
        setFilters,
        filters
    } = usePageTable<Revision>('created');
    const { page, pageSize } = pageConfig;
    const { checked } = tableValue;

    const { data, isFetching, refetch } = useDatasets(
        { searchText, sortConfig, page, size, filters },
        { cacheTime: 0 }
    );

    useEffect(() => {
        if (checkedValues) {
            onTableValueChange({
                ...tableValue,
                checked: checkedValues
            });
        }
    }, []);

    useEffect(() => {
        setSelectedRevisions(checked || []);
        if (onRevisionSelect) {
            onRevisionSelect(checked as number[]);
        }
    }, [checked]);

    useEffect(() => {
        if (onRevisionSelect) {
            onRevisionSelect(selectedRevisions as number[]);
        }
    }, [selectedRevisions]);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('revisions');
        if (localFilters) setFilters(localFilters);
    }, []);

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    useEffect(() => {
        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Revision, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'revisions');

            setFilters(filtersToSet);
        }
    }, [tableValue.filter]);

    useEffect(() => {
        refetch();
    }, [filters]);

    const { dataSource } = useAsyncSourceTable<Revision, number>(
        isFetching,
        data?.data ?? [],
        page,
        pageSize,
        searchText,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            checkbox: { isVisible: true },
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        }),
        sortBy: (dataset, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof Revision,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    useEffect(() => () => dataSource.unsubscribeView(onTableValueChange), []);

    const namesCache = useRef<PagingCache>({
        page: -1,
        cache: [],
        search: ''
    });

    type PagingCache = {
        page: number;
        cache: Array<string>;
        search: string;
    };

    const loadDatasetNames = createPagingCachedLoader<string, string>(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await datasetPropFetcher('name', pageNumber, pageSize, keyword)
    );

    const datasetNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadDatasetNames,
            getId: (name) => name
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, 'name'>(
        datasetNames,
        'name',
        { showSearch: true }
    );

    const renderCreationDateFilter = useDateRangeFilter('created');

    const columns = useMemo(() => {
        const nameColumn = revisionsColumns.find(({ key }) => key === 'name');
        nameColumn!.renderFilter = renderNameFilter;

        const createdDateColumn = revisionsColumns.find(({ key }) => key === 'created');
        createdDateColumn!.renderFilter = renderCreationDateFilter;

        return revisionsColumns;
    }, [revisionsColumns, renderNameFilter]);

    return (
        <div className={styles.wrapper}>
            <TableWrapper
                page={page}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={onPageChange}
            >
                <DataTable
                    {...view.getListProps()}
                    getRows={view.getVisibleRows}
                    value={tableValue}
                    onValueChange={onTableValueChange}
                    columns={columns}
                    headerTextCase="upper"
                />
            </TableWrapper>
        </div>
    );
};
