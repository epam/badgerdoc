import { useCallback, useMemo, useState } from 'react';
import { fetchWithTrackingOfUploadProgressFactory } from './fetch-with-tracking-of-upload-progress-factory';
import { BadgerCustomFetch } from 'api/hooks/api';
import { useNotifyProcessing } from './use-notify-processing';
import { NotificationTypes, showNotification } from 'shared/components/notifications';

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

const useHandleUploadError = (onError: () => void) => {
    return useCallback(() => {
        showNotification({
            type: NotificationTypes.error,
            text: 'Error uploading the file. Try again later.'
        });
        onError();
    }, [onError]);
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

    const handleError = useHandleUploadError(onError);

    const fetchWithTrackingOfUploadProgress: BadgerCustomFetch = useCallback(
        (url, reqParams) =>
            fetchWithTrackingOfUploadProgressFactory({
                onProgressCallback: setProgress,
                onError: handleError
            })(url, reqParams),
        [handleError]
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
