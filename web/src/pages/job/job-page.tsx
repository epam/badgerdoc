import React, { useState } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { JobConnector } from 'connectors/job-detail-view-connector/job-detail-view-connector';
import styles from './job-page.module.scss';
import { JobSidebarConnector } from '../../connectors/job-detail-view-sidebar-connector/job-detail-view-sidebar-connector';
import { Job } from '../../api/typings/jobs';
import qs from 'qs';
import { User } from 'api/typings';
import { JOBS_PAGE } from '../../shared/constants/general';

export function JobPage() {
    const history = useHistory();
    const { jobId } = useParams() as any;
    const [user, setUser] = useState<User>();
    const [activeTab, setActiveTab] = useState<string>('Files');
    let id = parseFloat(jobId) as number;

    const handleUserClick = (user?: User) => {
        setUser(user);
    };
    const handleExtractionJobClick = (id: number) => {
        history.push({
            pathname: `/documents/document`,
            search: qs.stringify({ jobId: jobId, documentId: id })
        });
    };
    const handleTaskClick = (id: number) => {
        history.push(`/dashboard/${id}`);
    };
    const getActiveTab = (tab: string) => {
        setActiveTab(tab);
    };

    const handleEditJobClick = (job: Job) => {
        history.push({
            pathname: `${JOBS_PAGE}/edit/${job.id}`
        });
    };

    return (
        <>
            <div className={styles['job-page-main-content']}>
                <div className={styles['job-page-sidebar-content']}>
                    <JobSidebarConnector
                        jobId={id}
                        onUserClick={handleUserClick}
                        activeUser={user}
                        activeTab={activeTab}
                    />
                </div>
                <div className={styles['job-page-table-content']}>
                    <JobConnector
                        onRowClick={handleExtractionJobClick}
                        onTaskClick={handleTaskClick}
                        onEditJobClick={handleEditJobClick}
                        jobId={id}
                        user={user}
                        getActiveTab={getActiveTab}
                    />
                </div>
            </div>
        </>
    );
}
