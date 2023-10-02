// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React from 'react';
import { Job } from 'api/typings/jobs';
import { Status } from 'shared/components/status';
import { FlexRow, Text } from '@epam/loveship';
import { DataColumnProps } from '@epam/uui';

import { mapStatusForJobs } from '../../shared/helpers/map-statuses';

export const jobColumns: DataColumnProps<Job>[] = [
    {
        key: 'name',
        caption: 'job name',
        render: (job: Job) => <Text fontSize="14">{job.name}</Text>,
        isSortable: true,
        grow: 3,
        shrink: 2,
        width: 100
    },
    {
        key: 'type',
        caption: 'Job Type',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (job: Job) => <Text fontSize="14">{job.type.replace('Job', '')}</Text>,
        width: 100
    },
    {
        key: 'status',
        caption: 'status',
        render: (job: Job) => (
            <FlexRow cx="align-baseline">
                {job.status && (
                    <Status
                        statusTitle={mapStatusForJobs(job.status, job.mode).title}
                        color={mapStatusForJobs(job.status, job.mode).color}
                    />
                )}
            </FlexRow>
        ),
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
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
        isSortable: true,
        width: 100
    },
    {
        key: 'creation_datetime',
        caption: 'Created Date',
        render: (job: Job) => (
            <Text fontSize="14">
                {job.creation_datetime ? new Date(job.creation_datetime).toLocaleDateString() : ''}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true,
        width: 100
    }
];
