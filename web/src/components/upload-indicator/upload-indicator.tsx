import { FC } from 'react';
import { IndeterminateBar } from '@epam/loveship';
import styles from './upload-indicator.module.scss';

export const UploadIndicator: FC<{ size?: '12' | '18' | '24' }> = ({ size }) => {
    return (
        <div className={styles['upload-indicator']}>
            <div className={styles['upload-bar']}>
                <IndeterminateBar size={size || '12'} />
            </div>
            <span>File is uploading!</span>
        </div>
    );
};
