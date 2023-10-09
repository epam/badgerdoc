import { FC } from 'react';
import { IndeterminateBar, ProgressBar } from '@epam/loveship';
import styles from './upload-indicator.module.scss';
import { UploadProgressTracker } from 'connectors/documents-page-control-connector/use-fetch-with-tracking-of-upload-progress';

export const UploadIndicator: FC<{
    uploadProgressTracker: UploadProgressTracker;
}> = ({ uploadProgressTracker }) => {
    const { isUploaded, progress } = uploadProgressTracker;

    const message = isUploaded ? 'Processing' : 'Uploading';
    const indicatorWrapperStyle = isUploaded ? styles.processing : styles.uploading;

    return (
        <div className={styles['upload-indicator']}>
            <div className={indicatorWrapperStyle}>
                {isUploaded ? <IndeterminateBar /> : <ProgressBar progress={progress} size="12" />}
                <span>{message}</span>
            </div>
        </div>
    );
};
