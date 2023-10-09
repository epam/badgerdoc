import { useCallback, useMemo, useState } from 'react';
import { fetchWithTrackingOfUploadProgressFactory } from './fetch-with-tracking-of-upload-progress-factory';
import { BadgerCustomFetch } from 'api/hooks/api';
export interface UploadProgressTracker {
    progress: number;
    setProgress: (progress: number) => void;
    isUploaded: boolean;
    resetUploadProgressState: () => void;
}

export const useFetchWithTrackingOfUploadProgress = (): {
    uploadProgressTracker: UploadProgressTracker;
    fetchWithTrackingOfUploadProgress: BadgerCustomFetch;
} => {
    const [progress, setProgress] = useState<number>(0);

    const isUploaded = progress === 100;

    const resetUploadProgressState = useCallback(() => {
        setProgress(0);
    }, []);

    const uploadProgressTracker: UploadProgressTracker = useMemo(
        () => ({
            progress,
            setProgress,
            isUploaded,
            resetUploadProgressState
        }),
        [progress, setProgress, isUploaded, resetUploadProgressState]
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const fetchWithTrackingOfUploadProgress = useCallback(
        fetchWithTrackingOfUploadProgressFactory({
            uploadProgressTracker
        }),
        [uploadProgressTracker]
    );

    return {
        uploadProgressTracker,
        fetchWithTrackingOfUploadProgress
    };
};
