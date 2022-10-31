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
    }
];
