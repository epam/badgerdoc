import React, { useState } from 'react';

import {
    DocumentPageSidebarContent,
    FileMetaInfo
} from './document-page-sidebar-content/document-page-sidebar-content';
import styles from './document-page.module.scss';
import { UseQueryResult } from 'react-query';
import { DocumentJob } from '../../api/typings/jobs';
import { DocumentJobRevisionsResponse } from '../../api/typings/revisions';
import { LazyDataSource } from '@epam/uui';
import TaskSidebar from '../../components/task/task-sidebar/task-sidebar';
import { TableAnnotatorContextProvider } from '../../shared/components/annotator/context/table-annotator-context';
import TaskDocumentPages from '../../components/task/task-document-pages/task-document-pages';
import { TaskAnnotatorContextProvider } from '../../connectors/task-annotator-connector/task-annotator-context';
import { useHistory } from 'react-router-dom';
import { DOCUMENTS_PAGE, JOBS_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants/general';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';
import { FlowSideBar } from 'components/task/task-sidebar-flow/task-sidebar-flow';
import { DocumentScale } from 'components/documents/document-scale/document-scale';

export interface DocumentPageProps {
    fileMetaInfo: FileMetaInfo;
    documentJobsInfo?: {
        documentJobDataSource: LazyDataSource<DocumentJob, number>;
        setSelectedDocumentJobId: React.Dispatch<React.SetStateAction<number | null>>;
        selectedDocumentJobId: number | null;
    };
    documentJobRevisionsInfo?: {
        documentJobRevisions: UseQueryResult<DocumentJobRevisionsResponse, unknown>;
        setSelectedDocumentJobRevisionId: React.Dispatch<React.SetStateAction<string>>;
        selectedDocumentJobRevisionId: string;
    };
    documentJobId?: number;
}

export function DocumentPage({
    fileMetaInfo,
    documentJobId,
    documentJobsInfo,
    documentJobRevisionsInfo
}: DocumentPageProps) {
    const [additionalScale, setAdditionalScale] = useState(0);

    const history = useHistory();

    const historyState = history.location.state as {
        previousPage?: string;
        previousPageUrl?: string;
        previousPageName?: string;
    };
    const crumbs = [];
    if (historyState?.previousPage === PREVIOUS_PAGE_JOB) {
        crumbs.push({ name: 'Extractions', url: JOBS_PAGE });
        crumbs.push({
            name: historyState.previousPageName || '',
            url: historyState.previousPageUrl
        });
    } else {
        crumbs.push({ name: 'Documents', url: DOCUMENTS_PAGE });
    }
    crumbs.push({ name: fileMetaInfo.name });

    return (
        <div className={styles['document-page']}>
            <div className={styles.header}>
                <div className={styles['header__left-block']}>
                    <BreadcrumbNavigation breadcrumbs={crumbs} />
                    <DocumentScale scale={additionalScale} onChange={setAdditionalScale} />
                </div>
            </div>
            <div className={styles['document-page-content']}>
                <TaskAnnotatorContextProvider
                    jobId={documentJobId}
                    revisionId={documentJobRevisionsInfo?.selectedDocumentJobRevisionId}
                    fileMetaInfo={fileMetaInfo}
                >
                    <TableAnnotatorContextProvider>
                        <FlowSideBar />
                        <TaskDocumentPages additionalScale={additionalScale} viewMode={true} />
                        <TaskSidebar
                            viewMode={true}
                            jobSettings={
                                <DocumentPageSidebarContent
                                    fileMetaInfo={fileMetaInfo}
                                    documentJobsInfo={documentJobsInfo}
                                    documentJobRevisionsInfo={documentJobRevisionsInfo}
                                />
                            }
                        />
                    </TableAnnotatorContextProvider>
                </TaskAnnotatorContextProvider>
            </div>
        </div>
    );
}
