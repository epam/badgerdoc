import { useCallback, useEffect, useState } from 'react';
import { useAnnotationsLazyLoading } from './use-annotations-lazy-loading';
import { useTokensLazyLoading } from './use-tokens-lazy-loading';
import { TDocumentDataLazyLoadingParams } from './types';

const createPendingPromise = () => {
    let resolver: (value: unknown) => void;
    const promise = new Promise((resolve) => {
        resolver = resolve;
    });

    return { promise, resolver: resolver! };
};

export const useDocumentDataLazyLoading = (
    {
        task,
        job,
        jobId,
        fileMetaInfo,
        revisionId,
        pageNumbers,
        setSelectedAnnotation
    }: TDocumentDataLazyLoadingParams,
    { enabled: hookEnabled }: { enabled: boolean }
) => {
    const [nextLoadingPagesRange, setNextLoadingPagesRange] = useState({ begin: -1, end: -1 });
    const [availableRenderedPagesRange, setAvailableRenderedPagesRange] = useState({
        begin: -1,
        end: -1
    });
    const [isDataLoadingPromise, setIsDataLoadingPromise] = useState(() => createPendingPromise());

    const nextLoadingPageNumbers = pageNumbers.slice(
        nextLoadingPagesRange.begin,
        nextLoadingPagesRange.end + 1
    );

    const {
        latestAnnotationsQuery,
        latestAnnotationsResultData,
        cachedPageIndexesRange: cachedAnnotationsPageIndexesRange,
        refetchLatestAnnotationsIfNeeded
    } = useAnnotationsLazyLoading(
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
        },
        { enabled: hookEnabled }
    );

    const getNextDocumentItems = async (startIndex: number, stopIndex: number) => {
        const pendingState = createPendingPromise();
        setIsDataLoadingPromise(pendingState);
        setNextLoadingPagesRange({ begin: startIndex, end: stopIndex });

        await pendingState.promise;
    };

    const {
        tokenQuery,
        tokenPages,
        cachedPageIndexesRange: cachedTokensPageIndexesRange
    } = useTokensLazyLoading(
        {
            task,
            fileMetaInfo,
            nextLoadingPageNumbers,
            pageNumbers,
            availableRenderedPagesRange,
            nextLoadingPagesRange
        },
        { enabled: hookEnabled }
    );

    useEffect(() => {
        if (hookEnabled && latestAnnotationsQuery.isSuccess && tokenQuery.isSuccess) {
            isDataLoadingPromise.resolver(undefined);
        }
    }, [latestAnnotationsQuery.isSuccess, tokenQuery.isSuccess, isDataLoadingPromise, hookEnabled]);

    // Our cached items are based on the range of loaded page indexes (based on first and last rendered page index),
    // not on the loaded data itself. It's done in such way because BE doesn't return any data for the
    // loading pages in case if they were not edited yet (no annotations were added yet). In such situation,
    // we assume that the data is actually loaded for the particular page in order to not make additional request
    // for it (without this since there are no data returned by BE, our loading mechanism will assume that it requires
    // additional request to load it). This is mostly a workaround and ideally BE should return to FE always some
    // data even in case if the page was not edited yet
    const isDocumentPageDataLoaded = useCallback(
        (index: number) =>
            cachedAnnotationsPageIndexesRange.begin <= index &&
            index <= cachedAnnotationsPageIndexesRange.end &&
            cachedTokensPageIndexesRange.begin <= index &&
            index <= cachedTokensPageIndexesRange.end,
        [cachedAnnotationsPageIndexesRange, cachedTokensPageIndexesRange]
    );

    return {
        latestAnnotationsResult: latestAnnotationsQuery,
        refetchLatestAnnotations: refetchLatestAnnotationsIfNeeded,
        latestAnnotationsResultData,
        availableRenderedPagesRange,
        tokenPages,
        setAvailableRenderedPagesRange,
        getNextDocumentItems,
        isDocumentPageDataLoaded
    };
};
