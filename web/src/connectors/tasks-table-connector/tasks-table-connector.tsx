import React, { FC, useContext, useEffect, useMemo } from 'react';
import { DataTable, Panel } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';
import { TableWrapper, usePageTable } from 'shared';
import { useTaskForDashboard } from 'api/hooks/tasks';
import { Task, TaskStatus } from 'api/typings/tasks';
import { COLUMNS } from './constants';
import { CurrentUser } from '../../shared/contexts/current-user';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Filter, FilterWithDocumentExtraOption, SortingDirection, TableFilters } from 'api/typings';
import { useColumnPickerFilter, useDateRangeFilter } from 'shared/components/filters/column-picker';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
import { DEFAULT_TABLE_FILTER } from './constants';
import { getTableFilter } from './utils';
import { useJobFilter } from './use-job-filter';
import { useNameFilter } from 'shared/hooks/use-name-filter';

type TaskTableConnectorProps = {
    onRowClick: (id: number) => void;
};
export const TasksTableConnector: FC<TaskTableConnectorProps> = ({ onRowClick }) => {
    const {
        pageConfig,
        onPageChange,
        totalCount,
        onTotalCountChange,
        tableValue,
        onTableValueChange,
        sortConfig,
        setSortConfig,
        setFilters,
        filters
    } = usePageTable<Task, TableFilters<Task, TaskStatus[] | boolean[]>>('id');

    const { page, pageSize } = pageConfig;
    const { currentUser } = useContext(CurrentUser);

    const statusesDS = useArrayDataSource<TaskStatus, string, unknown>(
        {
            items: ['Pending', 'Ready', 'In Progress', 'Finished'],
            getId: (status) => status
        },
        []
    );

    const typesDS = useArrayDataSource<boolean, string, unknown>(
        {
            items: [true, false],
            getId: (item) => item.toString()
        },
        []
    );

    const renderStatusFilter = useColumnPickerFilter<TaskStatus, string, unknown, 'status'>(
        statusesDS,
        'status'
    );

    const renderTypeFilter = useColumnPickerFilter<boolean, string, unknown, 'is_validation'>(
        typesDS,
        'is_validation',
        {
            showSearch: false,
            isPickByEntity: true,
            getName: (item) => (item ? 'Validation' : 'Annotation')
        }
    );

    const renderNameFilter = useNameFilter({
        fieldName: 'file_id'
    });

    const renderDeadlineFilter = useDateRangeFilter('deadline');

    const renderJobFilter = useJobFilter({ fieldName: 'job_id' });

    const columns = useMemo(() => {
        const statusColumn = COLUMNS.find(({ key }) => key === 'status');
        statusColumn!.isFilterActive = (filter) =>
            (filter.status && filter.status.in && !!filter.status.in.length) ?? false;
        statusColumn!.renderFilter = renderStatusFilter;

        const typeColumn = COLUMNS.find(({ key }) => key === 'is_validation');
        typeColumn!.isFilterActive = (filter) =>
            (filter.is_validation && filter.is_validation.in && !!filter.is_validation.in.length) ??
            false;
        typeColumn!.renderFilter = renderTypeFilter;

        const deadlineColumn = COLUMNS.find(({ key }) => key === 'deadline');
        deadlineColumn!.renderFilter = renderDeadlineFilter;

        const fileNameColumn = COLUMNS.find(({ key }) => key === 'file_name');
        fileNameColumn!.renderFilter = renderNameFilter;

        const jobColumn = COLUMNS.find(({ key }) => key === 'job_name');
        jobColumn!.renderFilter = renderJobFilter;

        return COLUMNS;
    }, []);

    useEffect(() => {
        let filter = DEFAULT_TABLE_FILTER;
        const localFilter = getFiltersFromStorage<Filter<keyof Task>[]>('tasks');

        if (localFilter) {
            setFilters(localFilter);
            filter = getTableFilter(localFilter);
        }

        onTableValueChange({
            ...tableValue,
            filter
        });

        return () => {
            dataSource.unsubscribeView(onTableValueChange);
        };
    }, []);

    const { data, isFetching } = useTaskForDashboard(
        { user_id: currentUser?.id, page, size: pageSize, sortConfig, filters },
        {
            cacheTime: 0
        }
    );

    useEffect(() => {
        if (tableValue.sorting && tableValue.sorting.length) {
            let { field, direction } = tableValue.sorting[0];
            if (field !== sortConfig.field || direction !== sortConfig.direction) {
                setSortConfig({
                    field: field as keyof Task,
                    direction: direction as SortingDirection
                });
            }
        }

        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Task, TaskStatus[] | boolean[]>(tableValue);
            saveFiltersToStorage(filtersToSet, 'tasks');
            setFilters(filtersToSet as (FilterWithDocumentExtraOption<keyof Task> | null)[]);
        }
    }, [tableValue.filter, tableValue.sorting, sortConfig]);

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    const { dataSource } = useAsyncSourceTable<Task, number>(
        isFetching,
        data?.data ?? [],
        page,
        pageSize,
        currentUser?.id,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        })
    });

    return (
        <>
            <Panel
                cx="flex-cell"
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': COLUMNS.length
                }}
            >
                <TableWrapper
                    page={page}
                    pageSize={pageSize}
                    totalCount={totalCount}
                    hasMore={data?.pagination.has_more}
                    onPageChange={onPageChange}
                >
                    <div>
                        <DataTable
                            {...view.getListProps()}
                            getRows={view.getVisibleRows}
                            value={tableValue}
                            onValueChange={onTableValueChange}
                            columns={columns}
                            headerTextCase="upper"
                        />
                    </div>
                </TableWrapper>
            </Panel>
        </>
    );
};
