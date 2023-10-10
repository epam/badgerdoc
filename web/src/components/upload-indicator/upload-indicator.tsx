import { FC, useEffect } from 'react';
import { IndeterminateBar, ProgressBar } from '@epam/loveship';
import styles from './upload-indicator.module.scss';
import { UploadProgressTracker } from 'connectors/documents-page-control-connector/use-fetch-with-tracking-of-upload-progress';

export const UploadIndicator: FC<{
    uploadProgressTracker: UploadProgressTracker;
}> = ({ uploadProgressTracker }) => {
    const message = uploadProgressTracker.isUploaded ? 'Processing...' : 'Uploading...';

    useEffect(() => {
        return () => {
            if (uploadProgressTracker.isUploaded) uploadProgressTracker.resetUploadProgressState();
        };
    }, [uploadProgressTracker]);

    return (
        <div className={styles['upload-indicator']}>
            {uploadProgressTracker.isUploaded ? (
                <div className={styles.bg}>
                    <div className={styles['indefinite-bar-wrapper']}>
                        <IndeterminateBar cx={styles.bg} />
                    </div>
                </div>
            ) : (
                <ProgressBar progress={uploadProgressTracker.progress} size="12" cx={styles.bg} />
            )}

            <span>{message}</span>
        </div>
    );
};
