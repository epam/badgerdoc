import React, { useEffect, useMemo } from 'react';
import styles from './job-sidebar-header.module.scss';
import { Job, JobType } from '../../../api/typings/jobs';
import { Status } from '../status';
import { mapStatusForJobs } from 'shared/helpers/map-statuses';
import '@epam/uui-components/styles.css';
import { useJobProgress } from 'api/hooks/jobs';

type JobSidebarHeaderProps = {
    job: Job | undefined;
};

const JobTypeLabel: Record<JobType, string> = {
    ExtractionJob: 'Automatic',
    AnnotationJob: 'Manual',
    ExtractionWithAnnotationJob: 'Automatic + Manual',
    ImportJob: 'Import'
};

export const JobSidebarHeader = ({ job }: JobSidebarHeaderProps) => {
    if (!job) return null;

    const { data, refetch } = useJobProgress({ jobId: job.id });

    const progress = useMemo(() => {
        if (data && data[job.id]?.finished && data[job.id]?.total) {
            return +(data[job.id]?.finished / data[job.id]?.total).toFixed(2) * 100;
        }
        return 0;
    }, [data]);

    useEffect(() => {
        if (
            progress < 100 ||
            (job.type === 'ExtractionWithAnnotationJob' && data?.[job.id]?.mode === 'Automatic')
        ) {
            refetch();
        }
    }, [data]);

    return (
        <div className={styles.sidebarHeaderWrapper}>
            <h2 className={styles.headerText}>{JobTypeLabel[job.type]}</h2>
            <div className={styles.jobStatusWrapper}>
                <Status
                    statusTitle={mapStatusForJobs(job.status ?? 'Pending', job.mode).title}
                    color={mapStatusForJobs(job.status ?? 'Pending', job.mode).color}
                />
            </div>

            <div style={{ flexBasis: '100%' }}>
                <p className={styles.progressBarText}>{`${progress}% processed`}</p>
                <div className={styles.root}>
                    <div style={{ width: `${progress}%` }} className={styles.bar}></div>
                </div>
            </div>
        </div>
    );
};
