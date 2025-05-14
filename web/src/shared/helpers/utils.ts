// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks, react-hooks/exhaustive-deps, @typescript-eslint/no-redeclare */
import { DataColumnProps, DataSourceState, useArrayDataSource } from '@epam/uui';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import {
    SortingDirection,
    Model,
    FilterWithDocumentExtraOption,
    PagedResponse,
    Sorting,
    TableFilters
} from '../../api/typings';
import { useColumnPickerFilter } from '../components/filters/column-picker';
import { useEffect, useMemo } from 'react';

export const getSource = <DataSourceType>(
    data: PagedResponse<DataSourceType> | undefined,
    tableValue: DataSourceState<TableFilters<DataSourceType, []>, any>,
    onTableValueChange: (data: DataSourceState<TableFilters<DataSourceType, []>, any>) => void,
    onRowClick: (id: number) => void,
    sortConfig: Sorting<keyof Model>,
    setSortConfig: (value: Sorting<keyof DataSourceType>) => void,
    isFetching: boolean,
    page: number,
    pageSize: number,
    searchText: string,
    filters: FilterWithDocumentExtraOption<keyof Model>[]
) => {
    const { dataSource } = useAsyncSourceTable<DataSourceType, any>(
        isFetching,
        data?.data ?? [],
        sortConfig,
        pageSize,
        page,
        searchText,
        filters
    );

    return dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        }),
        sortBy: (model, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof DataSourceType,
                    direction: direction as SortingDirection
                });
            }
        }
    });
};

export const buildFilterableColumns = (
    typeFilter: string,
    columnType: DataColumnProps<Model>[]
) => {
    const itemsParams = ['deployed', 'ready', 'failed', 'deploying'];
    const statusesDS = useArrayDataSource<string, string, unknown>(
        {
            items: itemsParams,
            getId: (status) => status
        },
        []
    );

    const renderStatusFilter = useColumnPickerFilter<string, string, unknown, string>(
        statusesDS,
        typeFilter
    );

    const filterColumn = [typeFilter];

    const columns = useMemo(() => {
        const statusColumn = columnType.filter(({ key }) => {
            return filterColumn.includes(key);
        });
        statusColumn.forEach((item) => {
            item!.isFilterActive = (filter) =>
                (filter.status && filter.status.in && !!filter.status.in.length) ?? false;
            item!.renderFilter = renderStatusFilter;
        });

        return columnType;
    }, []);

    return columns;
};

interface ITableValue<TFilter, TSorting> {
    filter?: TFilter | any;
    sorting?: TSorting | any;
    topIndex?: number;
    visibleCount?: number;
}

interface ISetSortConfig<DataType, TDirection> {
    field: DataType | any;
    direction: TDirection | SortingDirection;
}

interface ISetFilters<TField, TOperator, TValue> {
    field: TField | any;
    operator: TOperator | any;
    value: TValue | string;
}

export const applyTableConfigs = <TFilter, TSorting, TDirection, TOperator, TValue, DataType>(
    tableValue: ITableValue<TFilter, TSorting>,
    sortConfig: Record<string, string>,
    setSortConfig: (data: ISetSortConfig<DataType, TDirection>) => void,
    setFilters: (data: ISetFilters<DataType, TOperator, TValue>[]) => void
) => {
    if (tableValue.sorting && tableValue.sorting.length) {
        let { field, direction } = tableValue.sorting[0];
        if (field !== sortConfig.field || direction !== sortConfig.direction) {
            setSortConfig({
                field: field as keyof DataType,
                direction: direction as SortingDirection
            });
        }
    }
    if (tableValue.filter) {
        const field = Object.keys(tableValue.filter)[0] as keyof DataType;
        const operator = Object.keys(tableValue.filter[field]!)[0];
        const value = tableValue.filter[field]![operator]!;

        setFilters([{ field, operator, value }]);
    }
};
export const mapUndefString = (fn: (s: string) => void) => (val: string | undefined) =>
    fn(val || '');

export const useOutsideClick = (ref: any, callback: () => void) => {
    const handleClick = (e: { target: any }) => {
        if (ref.current && !ref.current.contains(e.target)) {
            callback();
        }
    };

    useEffect(() => {
        document.addEventListener('click', handleClick);

        return () => {
            document.removeEventListener('click', handleClick);
        };
    });
};

