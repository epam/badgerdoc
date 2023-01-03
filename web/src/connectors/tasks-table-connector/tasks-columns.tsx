import React from 'react';
import { Task } from '../../api/typings/tasks';
import { FlexRow, Text } from '@epam/loveship';
import { DataColumnProps } from '@epam/uui';
import { mapStatusForTasks } from 'shared/helpers/map-statuses';
import { Status } from 'shared/components/status';

export const tasksColumns: DataColumnProps<Task>[] = [
    {
        key: 'id',
        caption: 'Task ID',
        render: (task: Task) => <Text fontSize="14">{task.id}</Text>,
        isSortable: true,
        grow: 1,
        shrink: 1
    },
    {
        key: 'job_name',
        caption: 'Job Name',
        render: (task: Task) => <Text fontSize="14">{task.job.name}</Text>,
        isSortable: false,
        grow: 2,
        shrink: 2
    },
    {
        key: 'file_name',
        caption: 'File Name',
        render: (task: Task) => <Text fontSize="14">{task.file.name}</Text>,
        isSortable: false,
        grow: 2,
        shrink: 1
    },
    {
        key: 'status',
        caption: 'status',
        render: (task: Task) => (
            <FlexRow cx="align-baseline">
                <Status
                    statusTitle={mapStatusForTasks(task.status).title}
                    color={mapStatusForTasks(task.status).color}
                />
            </FlexRow>
        ),
        isSortable: true,
        grow: 1,
        shrink: 1
    },

    {
        key: 'is_validation',
        caption: 'Type',
        render: (task: Task) => (
            <Text fontSize="14">{task.is_validation ? 'Validation' : 'Annotation'}</Text>
        ),
        isSortable: true,
        grow: 1,
        shrink: 1
    },
    {
        key: 'pages',
        caption: 'Pages',
        render: (task: Task) => <Text fontSize="14">{task.pages.length}</Text>,
        grow: 1,
        shrink: 1
    },
    {
        key: 'deadline',
        caption: 'deadline',
        render: (task: Task) => (
            <Text fontSize="14">
                {task.deadline === null ? '' : new Date(task.deadline).toLocaleDateString()}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true
    }
];
