import React from 'react';
import { Button, FlexCell, FlexRow, FlexSpacer } from '@epam/loveship';
import { Job } from 'api/typings/jobs';
import styles from './job-header.module.scss';
import { JOBS_PAGE } from '../../constants';
import { BreadcrumbNavigation } from '../breadcrumb';

type JobDetailViewHeaderProps = {
    name: string;
    type: string;
    onCreateNewTaskClick(): void;
    onStartJob: () => void;
    job?: Job;
    onDistributeTaskClick(): void;
    onEditJobClick(job: Job): void;
};
// const JobTypeLabel: Record<JobType, string> = {
//     ExtractionJob: 'Automatic',
//     AnnotationJob: 'Manual',
//     ExtractionWithAnnotationJob: 'Automatic + Manual',
//     ImportJob: 'Import'
// };
export const JobDetailViewHeader: React.FC<JobDetailViewHeaderProps> = ({
    name,
    onCreateNewTaskClick,
    onStartJob,
    job,
    onDistributeTaskClick,
    onEditJobClick
}) => {
    if (!job) return null;

    const jobCanBeStarted =
        (job.status === 'Pending' && job.type === 'AnnotationJob') ||
        (job.status === 'Ready For Annotation' && job.type === 'ExtractionWithAnnotationJob');

    return (
        <FlexCell cx={styles.wrapper}>
            <FlexRow alignItems="center">
                <FlexRow cx={styles.container}>
                    <FlexRow alignItems="center">
                        <BreadcrumbNavigation
                            breadcrumbs={
                                name
                                    ? [{ name: 'Extractions', url: JOBS_PAGE }, { name: name }]
                                    : [{ name: 'Extractions', url: JOBS_PAGE }]
                            }
                        />
                    </FlexRow>
                    <FlexRow>
                        <Button caption="Edit" onClick={() => onEditJobClick(job)} />
                        {jobCanBeStarted ? <Button caption="Start Job" onClick={onStartJob} /> : ''}
                        <Button
                            caption="Distribute Tasks"
                            onClick={onDistributeTaskClick}
                            isDisabled={job.mode !== 'Manual'}
                        />
                        {job.type === 'AnnotationJob' ||
                        job.type === 'ExtractionWithAnnotationJob' ? (
                            <Button caption="Create Task" onClick={onCreateNewTaskClick} />
                        ) : (
                            ''
                        )}
                    </FlexRow>
                </FlexRow>
            </FlexRow>
            <FlexSpacer></FlexSpacer>
        </FlexCell>
    );
};
