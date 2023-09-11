import { useState } from 'react';
import { TRange } from './types';

export const useCachedDataPagesRange = () => {
    const [cachedPageIndexesRange, setCachedPageIndexesRange] = useState({ begin: -1, end: -1 });

    return {
        cachedPageIndexesRange,
        setCachedRange: (renderedPagesRange: TRange, loadingPagesRange: TRange) => {
            setCachedPageIndexesRange({
                begin: Math.min(loadingPagesRange.begin, renderedPagesRange.begin),
                end: Math.max(loadingPagesRange.end, renderedPagesRange.end)
            });
        }
    };
};
