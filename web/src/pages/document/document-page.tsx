// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { useCallback, useRef, useState } from 'react';

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
import { FlexRow } from '@epam/uui-components';

import { DocumentToolbar } from 'shared/components/document-toolbar';
import { TDocumentPDFRef } from 'shared/components/document-pages/components/document-pdf/types';

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
    const documentPDFRef = useRef<TDocumentPDFRef>(null);
    const [additionalScale, setAdditionalScale] = useState(0);
    const pages = fileMetaInfo.pages ?? 0;

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

    const onCurrentPageChange = useCallback((pageOrderNumber: number) => {
        documentPDFRef.current?.scrollDocumentTo(pageOrderNumber);
    }, []);

    return (
        <TaskAnnotatorContextProvider
            jobId={documentJobId}
            revisionId={documentJobRevisionsInfo?.selectedDocumentJobRevisionId}
            fileMetaInfo={fileMetaInfo}
            onRedirectAfterFinish={() => {}}
            onSaveTaskSuccess={() => {}}
            onSaveTaskError={() => {}}
        >
            <div className={styles['document-page']}>
                <div className={styles.header}>
                    <div className={styles['header__left-block']}>
                        <BreadcrumbNavigation breadcrumbs={crumbs} />
                        <FlexRow>
                            <DocumentToolbar
                                countOfPages={pages}
                                onPageChange={onCurrentPageChange}
                            ></DocumentToolbar>
                            <DocumentScale scale={additionalScale} onChange={setAdditionalScale} />
                        </FlexRow>
                    </div>
                </div>
                <div className={styles['document-page-content']}>
                    <TableAnnotatorContextProvider>
                        <FlowSideBar />
                        <TaskDocumentPages
                            additionalScale={additionalScale}
                            viewMode={true}
                            documentPDFRef={documentPDFRef}
                        />
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
                </div>
            </div>
        </TaskAnnotatorContextProvider>
    );
}
