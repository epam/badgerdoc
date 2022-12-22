import React, { useMemo } from 'react';
import { Task, TaskStatus } from '../../api/typings/tasks';
import { FlexRow, Text } from '@epam/loveship';
import { DataColumnProps, useArrayDataSource } from '@epam/uui';
import { TableFilters } from 'api/typings';
import { useColumnPickerFilter } from '../../shared/components/filters/column-picker';

const shTasksColumns: DataColumnProps<Task, any, TableFilters<Task, TaskStatus[] | boolean[]>>[] = [
    {
        key: 'file_name',
        caption: 'File Name',
        render: (task: Task) => <Text fontSize="14">{task.file.name}</Text>,
        grow: 2,
        shrink: 1
    },
    {
        key: 'status',
        caption: 'status',
        render: (task: Task) => (
            <FlexRow cx="align-baseline">
                <Text fontSize="14">{task.status}</Text>
            </FlexRow>
        ),
        isSortable: true,
        grow: 1,
        shrink: 1
    },
    {
        key: 'deadline',
        caption: 'Creation date',
        render: (task: Task) => (
            <Text fontSize="14">
                {task.deadline === null ? '' : new Date(task.deadline).toLocaleDateString()}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: false
    }
];

export const useColumns = () => {
    const statusesDS = useArrayDataSource<TaskStatus, string, unknown>(
        {
            items: ['Pending', 'Ready', 'In Progress', 'Finished'],
            getId: (status) => status
        },
        []
    );

    const renderStatusFilter = useColumnPickerFilter<TaskStatus, string, unknown, 'status'>(
        statusesDS,
        'status'
    );

    return useMemo(() => {
        const statusColumn = shTasksColumns.find(({ key }) => key === 'status');
        statusColumn!.isFilterActive = (filter) =>
            (filter.status && filter.status.in && !!filter.status.in.length) ?? false;
        statusColumn!.renderFilter = renderStatusFilter;

        return shTasksColumns;
    }, []);
};
