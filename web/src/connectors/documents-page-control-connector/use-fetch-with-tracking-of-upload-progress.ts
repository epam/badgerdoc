import { useCallback, useMemo, useState } from 'react';
import { fetchWithTrackingOfUploadProgressFactory } from './fetch-with-tracking-of-upload-progress-factory';
import { BadgerCustomFetch } from 'api/hooks/api';
export interface UploadProgressTracker {
    progress: number;
    setProgress: (progress: number) => void;
    isUploaded: boolean;
    resetUploadProgressState: () => void;
    fetchWithTrackingOfUploadProgress: BadgerCustomFetch;
}

export const useFetchWithTrackingOfUploadProgress = (): UploadProgressTracker => {
    const [progress, setProgress] = useState<number>(0);

    const isUploaded = progress === 100;

    const resetUploadProgressState = useCallback(() => {
        setProgress(0);
    }, []);

    const fetchWithTrackingOfUploadProgress: BadgerCustomFetch = useCallback(
        (url, reqParams) =>
            fetchWithTrackingOfUploadProgressFactory({
                onProgressCallback: setProgress
            })(url, reqParams),
        []
    );

    const uploadProgressTracker: UploadProgressTracker = useMemo(
        () => ({
            progress,
            setProgress,
            isUploaded,
            resetUploadProgressState,
            fetchWithTrackingOfUploadProgress
        }),
        [
            progress,
            setProgress,
            isUploaded,
            resetUploadProgressState,
            fetchWithTrackingOfUploadProgress
        ]
    );

    return uploadProgressTracker;
};
