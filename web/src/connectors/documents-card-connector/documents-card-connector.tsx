import React, { FC, useEffect, useState, useContext } from 'react';
import styles from './documents-card-connector.module.scss';
import { TableWrapper, usePageTable } from 'shared';
import { DocumentCardViewItem } from '../../components/documents/document-card-view-item/document-card-view-item';
import { usePieces } from 'api/hooks/search';
import { jobsFetcher } from '../../api/hooks/jobs';
import { Operators } from '../../api/typings';
import { Job } from '../../api/typings/jobs';
import { DocumentsSearch } from 'shared/contexts/documents-search';

type DocumentsCardConnectorProps = {
    onFilesSelect?: (files: number[]) => void;
};

export const DocumentsCardConnector: FC<DocumentsCardConnectorProps> = ({ onFilesSelect }) => {
    const { pageConfig, onPageChange, totalCount, onTotalCountChange } = usePageTable('category');
    const { query, facetFilter, documentsSort } = useContext(DocumentsSearch);
    const [jobs, setJobs] = useState<Job[]>();

    const { data: files } = usePieces({
        page: pageConfig.page,
        size: pageConfig.pageSize,
        searchText: query,
        sort: documentsSort,
        filter: facetFilter
    });

    useEffect(() => {
        if (files?.data?.length) {
            onTotalCountChange(files.pagination.total);
            jobsFetcher(1, 100, null, undefined, [
                {
                    field: 'id',
                    operator: Operators.IN,
                    value: files.data.map((e) => e.job_id)
                }
            ]).then((e) => setJobs(e.data));
        }
    }, [files]);

    if (files?.data.length && jobs) {
        return (
            <TableWrapper
                page={pageConfig.page}
                pageSize={pageConfig.pageSize}
                totalCount={totalCount}
                hasMore={files?.pagination.has_more}
                onPageChange={onPageChange}
            >
                <div className={styles['card-container']}>
                    {files.data.map(({ document_id, page_number, job_id, bbox }, index) => (
                        <DocumentCardViewItem
                            key={`${index}${document_id}`}
                            isPieces
                            documentId={document_id}
                            name={document_id}
                            documentPage={page_number}
                            jobs={jobs?.filter((e) => e.id == job_id)}
                            bbox={bbox}
                        />
                    ))}
                </div>
            </TableWrapper>
        );
    }

    return <div />;
};
