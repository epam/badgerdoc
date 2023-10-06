import { FC, useContext, useEffect } from 'react';
import { IndeterminateBar, ProgressBar } from '@epam/loveship';
import { UploadIndicatorContext } from './upload-indicator.context';
import styles from './upload-indicator.module.scss';

export const UploadIndicator: FC<{ isRequestOngoing: boolean }> = ({ isRequestOngoing }) => {
    const { progress, isUploaded, resetUploadProgressState } = useContext(UploadIndicatorContext);

    const Indicator = isUploaded ? (
        <IndeterminateBar />
    ) : (
        <ProgressBar progress={progress} size="12" />
    );

    const message = isUploaded ? 'Processing' : 'Uploading';

    const indicatorWrapperStyle = isUploaded ? styles.processing : styles.uploading;

    useEffect(() => {
        if (progress === 100 && isUploaded && !isRequestOngoing) {
            resetUploadProgressState();
        }
    }, [progress, isUploaded, isRequestOngoing, resetUploadProgressState]);

    return (
        <div className={styles['upload-indicator']}>
            <div className={indicatorWrapperStyle}>
                {Indicator}
                <span>{message}</span>
            </div>
        </div>
    );
};
