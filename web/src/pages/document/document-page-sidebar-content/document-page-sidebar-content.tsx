import React from 'react';

import { PendingContent } from '../../../shared';
import styles from './document-page-sidebar-content.module.scss';
import { UseQueryResult } from 'react-query';
import { DocumentJob } from '../../../api/typings/jobs';
import { LazyDataSource, useArrayDataSource } from '@epam/uui';
import { PickerInput } from '@epam/loveship';
import { DocumentJobRevisionsResponse } from '../../../api/typings/revisions';

export interface FileMetaInfo {
    id: number;
    name: string;
    pages: number | null;
    extension: string;
    lastModified: string | null;
    isLoading: boolean;
    imageSize?: { width: number; height: number };
}

export interface DocumentPageSidebarContentProps {
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
}

export const DocumentPageSidebarContent = ({
    fileMetaInfo,
    documentJobsInfo,
    documentJobRevisionsInfo
}: DocumentPageSidebarContentProps) => {
    const annotationsDataSource = useArrayDataSource(
        {
            items:
                documentJobRevisionsInfo &&
                Array.isArray(documentJobRevisionsInfo.documentJobRevisions.data)
                    ? documentJobRevisionsInfo.documentJobRevisions.data
                    : [],
            getId: (item) => item.revision
        },
        [documentJobRevisionsInfo?.documentJobRevisions.data]
    );

    return (
        <>
            <PendingContent loading={fileMetaInfo.isLoading}>
                {documentJobsInfo && (
                    <div className={styles['sidebar-picker']}>
                        <span
                            className={styles['sidebar-picker-header']}
                        >{`Extractions for document`}</span>
                        <div className={styles['sidebar-picker-body']}>
                            <PickerInput
                                dataSource={documentJobsInfo.documentJobDataSource}
                                value={documentJobsInfo.selectedDocumentJobId}
                                onValueChange={documentJobsInfo.setSelectedDocumentJobId}
                                selectionMode="single"
                                valueType="id"
                                minBodyWidth={100}
                                disableClear={true}
                            />
                        </div>
                    </div>
                )}
                {documentJobRevisionsInfo && (
                    <div className={styles['sidebar-picker']}>
                        <span className={styles['sidebar-picker-header']}>
                            {`Revisions for selected extraction`}
                        </span>
                        <div className={styles['sidebar-picker-body']}>
                            <PickerInput
                                onValueChange={
                                    documentJobRevisionsInfo.setSelectedDocumentJobRevisionId
                                }
                                getName={(item) => item?.revision ?? ''}
                                dataSource={annotationsDataSource}
                                valueType="id"
                                selectionMode="single"
                                value={documentJobRevisionsInfo.selectedDocumentJobRevisionId}
                                minBodyWidth={100}
                                disableClear={true}
                            />
                        </div>
                    </div>
                )}
            </PendingContent>
        </>
    );
};
