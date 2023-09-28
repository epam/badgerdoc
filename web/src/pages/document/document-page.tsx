// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { useCallback, useState } from 'react';

import {
    DocumentPageSidebarContent,
    FileMetaInfo
} from './document-page-sidebar-content/document-page-sidebar-content';
import styles from './document-page.module.scss';
import { UseQueryResult } from 'react-query';
import { DocumentJob } from '../../api/typings/jobs';
import { DocumentJobRevisionsResponse } from '../../api/typings/revisions';
import { LazyDataSource, useArrayDataSource } from '@epam/uui';
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
import { Button, FlexCell, PickerInput } from '@epam/loveship';

import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';

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
    const [goToPage, setGoToPage] = useState(1);
    const { pages } = fileMetaInfo;
    const isLastPage = goToPage === pages;
    const isFirstPage = goToPage === 1;

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

    const getPageNumbers = (pages = 1) => {
        const data: { [key: string]: any } = {};

        for (let i = 1; i <= pages; i++) {
            data[`_${i}`] = i;
        }

        return data;
    };

    const onPageChange = (page: any) => {
        setGoToPage(page);
    };

    const handleGoNext = useCallback(() => {
        isLastPage ? setGoToPage(pages) : setGoToPage((prev) => prev + 1);
    }, [goToPage, pages, isLastPage]);

    const handleGoPrev = useCallback(() => {
        isFirstPage ? setGoToPage(1) : setGoToPage((prev) => prev - 1);
    }, [goToPage, pages, isFirstPage]);

    const pagesDataSource = useArrayDataSource(
        {
            items: Object.values(getPageNumbers(pages!)),
            getId: (item) => item
        },
        []
    );

    crumbs.push({ name: fileMetaInfo.name });

    return (
        <div className={styles['document-page']}>
            <div className={styles.header}>
                <div className={styles['header__left-block']}>
                    <BreadcrumbNavigation breadcrumbs={crumbs} />
                    <FlexRow>
                        <FlexRow cx={styles['goto-page-selector']}>
                            <FlexCell minWidth={60}>
                                <span>Go to page</span>
                            </FlexCell>
                            <PickerInput
                                minBodyWidth={52}
                                size="24"
                                dataSource={pagesDataSource}
                                value={goToPage}
                                onValueChange={onPageChange}
                                getName={(item) => String(item)}
                                selectionMode="single"
                                disableClear={true}
                            />
                            <FlexRow>
                                <span>of {pages}</span>
                                <Button
                                    size="24"
                                    fill="white"
                                    icon={goPrevIcon}
                                    cx={styles.button}
                                    onClick={handleGoPrev}
                                    isDisabled={isFirstPage}
                                />
                                <Button
                                    size="24"
                                    fill="white"
                                    icon={goNextIcon}
                                    cx={styles.button}
                                    onClick={handleGoNext}
                                    isDisabled={isLastPage}
                                />
                            </FlexRow>
                        </FlexRow>
                        <DocumentScale scale={additionalScale} onChange={setAdditionalScale} />
                    </FlexRow>
                </div>
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
                        <FlowSideBar />
                        <TaskDocumentPages
                            additionalScale={additionalScale}
                            goToPage={goToPage}
                            viewMode={true}
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
                </TaskAnnotatorContextProvider>
            </div>
        </div>
    );
}
