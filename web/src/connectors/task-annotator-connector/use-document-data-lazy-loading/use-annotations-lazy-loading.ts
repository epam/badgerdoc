import { useState } from 'react';
import {
    AnnotationsResponse,
    useLatestAnnotations,
    useLatestAnnotationsFetcher
} from 'api/hooks/annotations';
import {
    getPageNumbersToKeepInCache,
    mergeCachedArraysBasedOnCachedNumbers
} from '../task-annotator-utils';
import { TAnnotationsLazyLoadingParams } from './types';
import { useCachedDataPagesRange } from './use-cached-data-pages-range';

const intersect = (a: number[], b: number[]) => {
    const setB = new Set(b);
    return [...new Set(a)].filter((x) => setB.has(x));
};

const mergeAnnotationsData = (
    oldData: AnnotationsResponse,
    newData: AnnotationsResponse,
    pageNumbersToKeepInCache: Set<number>
) => ({
    ...oldData,
    ...newData,
    pages: mergeCachedArraysBasedOnCachedNumbers(
        oldData.pages,
        newData.pages,
        pageNumbersToKeepInCache,
        ({ page_num }) => page_num
    ),
    validated: mergeCachedArraysBasedOnCachedNumbers(
        oldData.validated,
        newData.validated,
        pageNumbersToKeepInCache
    ),
    failed_validation_pages: mergeCachedArraysBasedOnCachedNumbers(
        oldData.failed_validation_pages,
        newData.failed_validation_pages,
        pageNumbersToKeepInCache
    )
});

export const useAnnotationsLazyLoading = (
    {
        task,
        job,
        jobId,
        fileMetaInfo,
        revisionId,
        nextLoadingPageNumbers,
        pageNumbers,
        availableRenderedPagesRange,
        nextLoadingPagesRange,
        setSelectedAnnotation
    }: TAnnotationsLazyLoadingParams,
    { enabled: hookEnabled }: { enabled: boolean }
) => {
    const [latestAnnotationsResultData, setLatestAnnotationsResultData] =
        useState<AnnotationsResponse>();
    const getJobId = () => (task ? task.job.id : jobId);
    const getFileId = () => (task ? task.file.id : fileMetaInfo?.id);

    const { cachedPageIndexesRange, setCachedRange } = useCachedDataPagesRange();
    const latestAnnotationsQueryParams = {
        jobId: getJobId(),
        fileId: getFileId(),
        revisionId,
        pageNumbers: nextLoadingPageNumbers,
        userId: job?.validation_type === 'extensive_coverage' && !revisionId ? task?.user_id : ''
    };

    const latestAnnotationsQuery = useLatestAnnotations(latestAnnotationsQueryParams, {
        enabled:
            hookEnabled && Boolean(task || job || revisionId) && nextLoadingPageNumbers.length > 0,
        cacheTime: 0,
        onSuccess(newData) {
            setLatestAnnotationsResultData((oldData) => {
                setCachedRange(availableRenderedPagesRange, nextLoadingPagesRange);

                if (!oldData) {
                    return newData;
                }

                const pageNumbersToKeepInCache = getPageNumbersToKeepInCache(
                    pageNumbers,
                    availableRenderedPagesRange
                );

                // unset selected annotation if it's not in cache (we render only items which are in cache)
                setSelectedAnnotation((prevSelectedAnnotation) => {
                    const noSelectedAnnotationInCache =
                        prevSelectedAnnotation &&
                        !pageNumbersToKeepInCache.has(prevSelectedAnnotation.pageNum!);

                    return noSelectedAnnotationInCache ? undefined : prevSelectedAnnotation;
                });

                // merge old cached data with the new received data
                return mergeAnnotationsData(oldData, newData, pageNumbersToKeepInCache);
            });
        }
    });

    const latestAnnotationsFetcher = useLatestAnnotationsFetcher();
    const refetchLatestAnnotationsIfNeeded = async (pageNumbersToRefetch: number[]) => {
        const cachedPageNumbers = pageNumbers.slice(
            cachedPageIndexesRange.begin,
            cachedPageIndexesRange.end + 1
        );
        const pageNumbersToFetch = intersect(cachedPageNumbers, pageNumbersToRefetch);

        if (pageNumbersToFetch.length > 0) {
            const newData = await latestAnnotationsFetcher({
                ...latestAnnotationsQueryParams,
                pageNumbers: pageNumbersToFetch
            });

            setLatestAnnotationsResultData((oldData) =>
                mergeAnnotationsData(oldData!, newData, new Set(cachedPageNumbers))
            );
        }
    };

    return {
        latestAnnotationsQuery,
        latestAnnotationsResultData,
        refetchLatestAnnotationsIfNeeded,
        cachedPageIndexesRange
    };
};
