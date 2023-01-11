import React, { FC, useContext, useEffect, useMemo } from 'react';
import { DataTable, Panel } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';
import { TableWrapper, usePageTable } from 'shared';
import { useTaskForDashboard } from 'api/hooks/tasks';
import { Task, TaskStatus } from 'api/typings/tasks';
import { tasksColumns } from './tasks-columns';
import { CurrentUser } from '../../shared/contexts/current-user';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Operators, SortingDirection, TableFilters } from 'api/typings';
import { useColumnPickerFilter, useDateRangeFilter } from 'shared/components/filters/column-picker';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';

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

    const typesDSItems = [
        {
            name: true,
            id: true
        },
        {
            name: false,
            id: false
        }
    ];

    const typesDS = useArrayDataSource<any, boolean, unknown>(
        {
            items: typesDSItems
        },
        []
    );

    const renderStatusFilter = useColumnPickerFilter<TaskStatus, string, unknown, 'status'>(
        statusesDS,
        'status'
    );

    const renderTypeFilter = useColumnPickerFilter<boolean, boolean, unknown, 'is_validation'>(
        typesDS,
        'is_validation',
        {
            showSearch: false,
            isPickByEntity: true,
            getName: (item: boolean) => (item ? 'Validation' : 'Annotation')
        }
    );

    const renderDeadlineFilter = useDateRangeFilter('deadline');

    const columns = useMemo(() => {
        const statusColumn = tasksColumns.find(({ key }) => key === 'status');
        statusColumn!.isFilterActive = (filter) =>
            (filter.status && filter.status.in && !!filter.status.in.length) ?? false;
        statusColumn!.renderFilter = renderStatusFilter;

        const typeColumn = tasksColumns.find(({ key }) => key === 'is_validation');
        typeColumn!.isFilterActive = (filter) =>
            (filter.is_validation && filter.is_validation.in && !!filter.is_validation.in.length) ??
            false;
        typeColumn!.renderFilter = renderTypeFilter;

        const deadlineColumn = tasksColumns.find(({ key }) => key === 'deadline');
        deadlineColumn!.renderFilter = renderDeadlineFilter;

        return tasksColumns;
    }, []);

    useEffect(() => {
        const localFilter = getFiltersFromStorage('tasks');
        if (localFilter) setFilters(localFilter);
        else
            onTableValueChange({
                ...tableValue,
                filter: {
                    status: { [Operators.IN]: ['Ready', 'In Progress'] },
                    is_validation: { [Operators.IN]: [true, false] }
                }
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
            setFilters(filtersToSet);
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
                    'aria-colcount': tasksColumns.length
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
