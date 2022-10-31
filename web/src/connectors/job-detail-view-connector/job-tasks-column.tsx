import { Task } from '../../api/typings/tasks';
import { FlexRow, Text } from '@epam/loveship';
import React from 'react';

export default [
    {
        key: 'name',
        caption: 'User ID',
        render: (task: Task) => <Text fontSize="14">{task.user_id || 'Unassigned'}</Text>,
        isSortable: true,
        grow: 2,
        shrink: 2
    },
    {
        key: 'file_name',
        caption: 'File Name',
        render: (task: Task) => <Text fontSize="14">{task.file.name}</Text>,
        isSortable: true,
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
        isSortable: true,
        grow: 1,
        shrink: 1
    },
    {
        key: 'deadline',
        caption: 'deadline',
        render: (task: Task) => (
            <Text fontSize="14">{new Date(task.deadline).toLocaleDateString()}</Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: false
    }
];
