import React, { useState } from 'react';
import { useJobs } from '../../api/hooks/jobs';
import { Operators, SortingDirection } from '../../api/typings';
import { Job } from '../../api/typings/jobs';
import { ModelTrainingJobs } from '../../components/model/model-training-jobs/model-training-jobs';
import { FlexCell, FlexRow, IconButton } from '@epam/loveship';
import { ReactComponent as ArrowDown } from '@epam/assets/icons/common/navigation-arrow-down-18.svg';
import { ReactComponent as ArrowRight } from '@epam/assets/icons/common/navigation-arrow-right-18.svg';
import styles from './training-jobs-connector.module.scss';

type TrainingJobsConnectorProps = {
    jobs: number[];
};

export const TrainingJobsConnector: React.FC<TrainingJobsConnectorProps> = ({ jobs }) => {
    const filters = [
        {
            field: 'id' as keyof Job,
            operator: Operators.IN,
            value: jobs
        }
    ];

    const [open, setOpen] = useState(false);

    const { data: jobsArray } = useJobs(
        {
            page: 1,
            size: jobs.length,
            filters,
            searchText: '',
            sortConfig: {
                field: 'id',
                direction: SortingDirection.DESC
            }
        },
        {}
    );
    return (
        <div className={styles.container}>
            <FlexRow>
                <FlexCell grow={1}>Jobs</FlexCell>
                <FlexCell cx="m-r-5" minWidth={20}>
                    <IconButton
                        icon={open ? ArrowDown : ArrowRight}
                        onClick={() => setOpen(!open)}
                    />
                </FlexCell>
            </FlexRow>
            {open && <ModelTrainingJobs jobs={jobsArray?.data || []} />}
        </div>
    );
};
