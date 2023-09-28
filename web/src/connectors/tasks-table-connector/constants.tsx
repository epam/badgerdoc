// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React from 'react';
import { FlexRow, Text } from '@epam/loveship';
import { DataColumnProps } from '@epam/uui';
import { mapStatusForTasks } from 'shared/helpers/map-statuses';
import { Status } from 'shared/components/status';
import { Operators, TableFilters } from 'api/typings';
import { Task, TaskStatus } from 'api/typings/tasks';
import { ReactComponent as Copy } from '@epam/assets/icons/common/copy_content-12.svg';
import { handleCopy } from 'shared/helpers/copy-text';
import styles from './tasks-table.module.scss';

export const COLUMNS: DataColumnProps<Task>[] = [
    {
        key: 'id',
        caption: 'Task ID',
        render: (task: Task) => <Text>{task.id}</Text>,
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'job_name',
        caption: 'Job Name',
        render: (task: Task) => <Text>{task.job.name}</Text>,
        isSortable: false,
        grow: 2,
        shrink: 2,
        width: 100
    },
    {
        key: 'file_name',
        caption: 'File Name',
        render: (task: Task) => (
            <FlexRow>
                <Text cx={styles.fileName}>{task.file.name}</Text>
                <Copy onClick={(e) => handleCopy(e, task.file.name)} />
            </FlexRow>
        ),
        isSortable: false,
        grow: 2,
        shrink: 1,
        width: 200
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
        shrink: 1,
        width: 100
    },

    {
        key: 'is_validation',
        caption: 'Type',
        render: (task: Task) => <Text>{task.is_validation ? 'Validation' : 'Annotation'}</Text>,
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'pages',
        caption: 'Pages',
        render: (task: Task) => <Text>{task.pages.length}</Text>,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'deadline',
        caption: 'deadline',
        render: (task: Task) => (
            <Text>
                {task.deadline === null ? '' : new Date(task.deadline).toLocaleDateString()}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true,
        width: 100
    }
];

export const DEFAULT_TABLE_FILTER: TableFilters<Task, boolean[] | TaskStatus[]> = {
    status: { [Operators.IN]: ['Ready', 'In Progress'] },
    is_validation: { [Operators.IN]: [true, false] }
};
