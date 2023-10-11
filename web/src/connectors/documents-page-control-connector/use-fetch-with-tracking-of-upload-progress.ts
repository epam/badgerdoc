import { useCallback, useMemo, useState } from 'react';
import { fetchWithTrackingOfUploadProgressFactory } from './fetch-with-tracking-of-upload-progress-factory';
import { BadgerCustomFetch } from 'api/hooks/api';
import { useNotifyProcessing } from './use-notify-processing';

export interface UploadProgressTracker {
    progress: number;
    setProgress: (progress: number) => void;
    isUploaded: boolean;
    resetUploadProgressState: () => void;
    fetchWithTrackingOfUploadProgress: BadgerCustomFetch;
}

type UseFetchWithTrackingOfUploadProgressDeps = {
    onError: () => void;
};

export const useFetchWithTrackingOfUploadProgress = ({
    onError
}: UseFetchWithTrackingOfUploadProgressDeps): UploadProgressTracker => {
    const [progress, setProgress] = useState<number>(0);

    const isUploaded = progress === 100;

    useNotifyProcessing(isUploaded);

    const resetUploadProgressState = useCallback(() => {
        setProgress(0);
    }, []);

    const fetchWithTrackingOfUploadProgress: BadgerCustomFetch = useCallback(
        (url, reqParams) =>
            fetchWithTrackingOfUploadProgressFactory({
                onProgressCallback: setProgress,
                onError
            })(url, reqParams),
        [onError]
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
