import { useTokens } from 'api/hooks/tokens';
import { useState } from 'react';
import {
    getPageNumbersToKeepInCache,
    mergeCachedArraysBasedOnCachedNumbers
} from '../task-annotator-utils';
import { PageInfo } from 'api/typings';
import { TTokensLazyLoadingParams } from './types';
import { useCachedDataPagesRange } from './use-cached-data-pages-range';

export const useTokensLazyLoading = (
    {
        task,
        fileMetaInfo,
        nextLoadingPageNumbers,
        pageNumbers,
        availableRenderedPagesRange,
        nextLoadingPagesRange
    }: TTokensLazyLoadingParams,
    { enabled: hookEnabled }: { enabled: boolean }
) => {
    const getFileId = () => (task ? task.file.id : fileMetaInfo?.id);
    const [tokenPages, setTokenPages] = useState<PageInfo[]>([]);

    const { cachedPageIndexesRange, setCachedRange } = useCachedDataPagesRange();

    const tokenQuery = useTokens(
        {
            fileId: getFileId(),
            pageNumbers: nextLoadingPageNumbers
        },
        {
            enabled: hookEnabled && nextLoadingPageNumbers.length > 0,
            cacheTime: 0,
            onSuccess: (newData) => {
                setTokenPages((oldData) => {
                    setCachedRange(availableRenderedPagesRange, nextLoadingPagesRange);

                    if (!oldData) {
                        return newData;
                    }

                    const pageNumbersToKeepInCache = getPageNumbersToKeepInCache(
                        pageNumbers,
                        availableRenderedPagesRange
                    );

                    return mergeCachedArraysBasedOnCachedNumbers(
                        oldData,
                        newData,
                        pageNumbersToKeepInCache,
                        (page) => page.page_num
                    );
                });
            }
        }
    );

    return { tokenQuery, tokenPages, cachedPageIndexesRange };
};
