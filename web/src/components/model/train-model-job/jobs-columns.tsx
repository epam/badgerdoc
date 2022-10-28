import { Text } from '@epam/loveship';
import React from 'react';
import { Job } from 'api/typings/jobs';
import { DataColumnProps } from '@epam/uui';

export const jobColumns: DataColumnProps<Job>[] = [
    {
        key: 'name',
        caption: 'extraction name',
        render: (job: Job) => <Text fontSize="14">{job.name}</Text>,
        isSortable: true,
        grow: 3,
        shrink: 2
    },
    {
        key: 'created_date',
        caption: 'Date',
        render: (job: Job) => (
            <Text fontSize="14">
                {job.creation_datetime ? new Date(job.creation_datetime).toLocaleDateString() : ''}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true
    },
    {
        key: 'deadline',
        caption: 'deadline',
        render: (job: Job) => (
            <Text fontSize="14">
                {job.deadline ? new Date(job.deadline).toLocaleDateString() : ''}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true
    }
];
