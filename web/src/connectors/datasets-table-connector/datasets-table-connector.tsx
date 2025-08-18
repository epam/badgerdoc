// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import { DataTable } from '@epam/loveship';
import React, { FC, useEffect, useMemo, useRef, useState } from 'react';
import { useArrayDataSource, useLazyDataSource } from '@epam/uui';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Dataset, SortingDirection } from 'api/typings';
import { pageSizes, TableWrapper, usePageTable } from 'shared';
import { datasetsColumns } from './datasets-columns';
import {
    useColumnPickerFilter,
    useDateRangeFilter
} from '../../shared/components/filters/column-picker';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
import { datasetPropFetcher, useDatasets } from 'api/hooks/datasets';

//TODO: move out styles from the connector
import styles from './datasets-table-connector.module.scss';

type DatasetsTableConnectorProps = {
    onRowClick: (id: number) => void;
    onDatasetSelect?: (dataset: number[]) => void;
    checkedValues?: number[] | string[];
};
const size = pageSizes._100;

export const DatasetsTableConnector: FC<DatasetsTableConnectorProps> = ({
    onRowClick,
    onDatasetSelect,
    checkedValues
}) => {
    const [selectedFiles, setSelectedFiles] = useState<number[] | []>([]);
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
    } = usePageTable<Dataset>('created');
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
        setSelectedFiles(checked || []);
        if (onDatasetSelect) {
            onDatasetSelect(checked as number[]);
        }
    }, [checked]);

    useEffect(() => {
        if (onDatasetSelect) {
            onDatasetSelect(selectedFiles as number[]);
        }
    }, [selectedFiles]);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('datasets');
        if (localFilters) setFilters(localFilters);
    }, []);

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    useEffect(() => {
        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Dataset, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'datasets');

            setFilters(filtersToSet);
        }
    }, [tableValue.filter]);

    useEffect(() => {
        refetch();
    }, [filters]);

    const { dataSource } = useAsyncSourceTable<Dataset, number>(
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
                    field: field as keyof Dataset,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    useEffect(() => () => dataSource.unsubscribeView(onTableValueChange), []);

    const datasetNames = useArrayDataSource<string, string, unknown>(
        {
            items: data?.data.map((d) => d.name) ?? [],
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
        const nameColumn = datasetsColumns.find(({ key }) => key === 'name');
        nameColumn!.renderFilter = renderNameFilter;

        const createdDateColumn = datasetsColumns.find(({ key }) => key === 'created');
        createdDateColumn!.renderFilter = renderCreationDateFilter;

        return datasetsColumns;
    }, [datasetsColumns, renderCreationDateFilter, renderNameFilter]);

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
