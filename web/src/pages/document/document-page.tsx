import React from 'react';

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
import { DOCUMENTS_PAGE, JOBS_PAGE, PREVIOUS_PAGE_JOB } from '../../shared/constants';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';

export interface DocumentPageProps {
    fileMetaInfo: FileMetaInfo;
    documentJobsInfo?: {
        documentJobDataSource: LazyDataSource<DocumentJob, number>;
        setSelectedDocumentJobId: React.Dispatch<React.SetStateAction<number | undefined>>;
        selectedDocumentJobId?: number;
    };
    documentJobRevisionsInfo?: {
        documentJobRevisions: UseQueryResult<DocumentJobRevisionsResponse, unknown>;
        setSelectedDocumentJobRevisionId: React.Dispatch<React.SetStateAction<string>>;
        selectedDocumentJobRevisionId: string;
    };
    documentJobId?: number;
}

export function DocumentPage(props: DocumentPageProps) {
    const { fileMetaInfo, documentJobsInfo, documentJobRevisionsInfo, documentJobId } = props;
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
            <div className={styles['document-page-subheader']}>
                <BreadcrumbNavigation breadcrumbs={crumbs} />
            </div>
            <div className={styles['document-page-content']}>
                <TaskAnnotatorContextProvider
                    jobId={documentJobId}
                    revisionId={documentJobRevisionsInfo?.selectedDocumentJobRevisionId}
                    fileMetaInfo={fileMetaInfo}
                    onRedirectAfterFinish={() => {}}
                    onSaveTaskSuccess={() => {}}
                    onSaveTaskError={() => {}}
                >
                    <TableAnnotatorContextProvider>
                        <TaskDocumentPages viewMode={true} />
                        <TaskSidebar
                            viewMode={true}
                            onRedirectAfterFinish={() => {}}
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
