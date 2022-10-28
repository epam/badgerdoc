import React from 'react';
import styles from './model-training-jobs.module.scss';
import { DataTable, Panel } from '@epam/loveship';
import { jobColumns } from './jobs-columns';
import { usePageTable } from '../../../shared';
import { Job } from '../../../api/typings/jobs';
import { useArrayDataSource } from '@epam/uui';

type ModelTrainingJobsProps = {
    jobs: Job[];
};

export const ModelTrainingJobs: React.FC<ModelTrainingJobsProps> = ({ jobs }) => {
    const { tableValue, onTableValueChange } = usePageTable<Job>('id');

    const source = useArrayDataSource<Job, number, unknown>(
        {
            items: jobs
        },
        [jobs]
    );

    const view = source.useView(tableValue, onTableValueChange);

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <Panel
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': jobColumns.length
                }}
            >
                <DataTable
                    {...view.getListProps()}
                    getRows={view.getVisibleRows}
                    value={tableValue}
                    onValueChange={onTableValueChange}
                    columns={jobColumns}
                    headerTextCase="upper"
                />
            </Panel>
        </Panel>
    );
};
