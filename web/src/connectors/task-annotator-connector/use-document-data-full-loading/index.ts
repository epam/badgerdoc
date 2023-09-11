import { AnnotationsResponse, useLatestAnnotations } from 'api/hooks/annotations';
import { useTokensFullLoading } from './use-tokens-full-loading';
import { TDocumentDataFullLoadingParams } from './types';
import { useEffect, useMemo, useRef, useState } from 'react';

const functionStub = () => {};

export const useDocumentDataFullLoading = (
    { revisionId, pageNumbers, task, job, jobId, fileMetaInfo }: TDocumentDataFullLoadingParams,
    { enabled: hookEnabled }: { enabled: boolean }
) => {
    const [latestAnnotationsResultData, setLatestAnnotationsResultData] =
        useState<AnnotationsResponse>();
    const getJobId = () => (task ? task.job.id : jobId);
    const getFileId = () => (task ? task.file.id : fileMetaInfo?.id);

    const { tokenPages, tokenRes } = useTokensFullLoading(
        { pageNumbers, task, fileMetaInfo },
        { enabled: hookEnabled }
    );
    const latestAnnotationsResult = useLatestAnnotations(
        {
            jobId: getJobId(),
            fileId: getFileId(),
            revisionId,
            pageNumbers,
            userId:
                job?.validation_type === 'extensive_coverage' && !revisionId ? task?.user_id : ''
        },
        {
            enabled: hookEnabled && Boolean(task || job),
            onSuccess: (data) => setLatestAnnotationsResultData(data)
        }
    );

    const documentDataRefetcher = useRef(() => {
        latestAnnotationsResult.refetch();
        tokenRes.refetch();
    });

    useEffect(() => {
        if (!hookEnabled) {
            return;
        }

        if (task || job || revisionId) {
            documentDataRefetcher.current();
        }
    }, [task, job, revisionId, hookEnabled]);

    const availableRenderedPagesRange = useMemo(
        () => ({ begin: 0, end: pageNumbers.length - 1 }),
        [pageNumbers]
    );

    return {
        tokenPages,
        latestAnnotationsResult,
        latestAnnotationsResultData,
        availableRenderedPagesRange,
        setAvailableRenderedPagesRange: functionStub,
        getNextDocumentItems: functionStub,
        isDocumentPageDataLoaded: () => true
    };
};
