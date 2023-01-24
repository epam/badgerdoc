import React, { useCallback, useEffect, useState } from 'react';
import { DocumentPage } from '../../pages';
import { useDocuments } from '../../api/hooks/documents';
import { Filter, Operators } from '../../api/typings';
import { documentSearchResultMapper } from '../../shared/helpers/document-search-result-mapper';
import { documentJobsFetcher, useDocumentJobsRevisions } from '../../api/hooks/document';
import { useHistory } from 'react-router';
import { DocumentJob } from '../../api/typings/jobs';
import qs from 'qs';
import { parseDate } from '../../shared/helpers/parse-date';
import { useEntity } from 'shared/hooks/use-entity';
import { useParams } from 'react-router-dom';

export const DocumentPageConnector = () => {
    const { documentId } = useParams<{ documentId: string }>();
    const history = useHistory();
    const query = qs.parse(history.location.search, { ignoreQueryPrefix: true }) as {
        revisionId?: string;
        jobId?: string;
    };
    const { revisionId, jobId } = query;
    const documentSearchResult = useDocuments(
        {
            filters: [
                {
                    field: 'id',
                    operator: Operators.EQ,
                    value: documentId
                }
            ]
        },
        { enabled: !!documentId }
    );
    const fileMetaInfo = {
        ...documentSearchResultMapper(documentSearchResult.data),
        isLoading: documentSearchResult.isLoading
    };

    const documentJobsFilters: Filter<keyof DocumentJob>[] = [
        { value: [Number(documentId || '')], operator: Operators.EQ, field: 'files' }
    ];

    const { dataSource: documentJobDataSource, cache: documentJobsCache } = useEntity<
        DocumentJob,
        number
    >(documentJobsFetcher, documentJobsFilters);

    const [selectedDocumentJobId, setSelectedDocumentJobId] = useState<number | undefined>(
        undefined
    );
    const [selectedDocumentJobRevisionId, setSelectedDocumentJobRevisionId] = useState('');
    const [documentJobId, setDocumentJobId] = useState<number>(Number(jobId));

    useEffect(() => {
        if (!documentJobId) {
            documentJobsFetcher(1, 100, '', documentJobsFilters).then(({ data }) => {
                setDocumentJobId(data[0]?.id);
            });
        }
    }, []);

    useEffect(() => {
        if (jobId && !selectedDocumentJobId) {
            setSelectedDocumentJobId(+jobId);
            return;
        }

        setSelectedDocumentJobRevisionId('');
    }, [selectedDocumentJobId, jobId]);

    const onDocumentJobSelect = useCallback(
        (documentJobId) => {
            setSelectedDocumentJobId(documentJobId);
        },
        [documentJobsCache.current]
    );

    const documentJobRevisions = useDocumentJobsRevisions(
        { documentId: documentId || '', jobId: selectedDocumentJobId! },
        { enabled: !!selectedDocumentJobId }
    );

    useEffect(() => {
        if (revisionId && !selectedDocumentJobRevisionId && selectedDocumentJobId) {
            setSelectedDocumentJobRevisionId(revisionId);
            return;
        }
        if (selectedDocumentJobRevisionId !== revisionId) {
            history.replace({
                pathname: history.location.pathname,
                search: qs.stringify({
                    ...qs.parse(history.location.search, { ignoreQueryPrefix: true }),
                    revisionId: selectedDocumentJobRevisionId
                }),
                state: history.location.state
            });
        }
        if (
            selectedDocumentJobId &&
            !selectedDocumentJobRevisionId &&
            documentJobRevisions.data &&
            Array.isArray(documentJobRevisions.data)
        ) {
            const { data } = documentJobRevisions;

            data.sort((a, b) => parseDate(b.date) - parseDate(a.date));

            setSelectedDocumentJobRevisionId(documentJobRevisions.data[0]?.revision);
        }
    }, [
        selectedDocumentJobRevisionId,
        revisionId,
        selectedDocumentJobId,
        documentJobRevisions.data
    ]);

    return (
        <DocumentPage
            fileMetaInfo={fileMetaInfo}
            documentJobsInfo={{
                documentJobDataSource,
                selectedDocumentJobId,
                setSelectedDocumentJobId: onDocumentJobSelect
            }}
            documentJobRevisionsInfo={{
                documentJobRevisions,
                selectedDocumentJobRevisionId,
                setSelectedDocumentJobRevisionId
            }}
            documentJobId={documentJobId}
        />
    );
};
