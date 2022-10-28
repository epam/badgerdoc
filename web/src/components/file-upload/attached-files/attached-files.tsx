import React, { FC } from 'react';
import { FileTag } from '../file-tag/file-tag';

import styles from './attached-files.module.scss';

type AttachedFilesProps = {
    files: File[];
    // files: { name: string; size: number | undefined }[];
    onFileRemove(file: File): void;
};

export const AttachedFiles: FC<AttachedFilesProps> = ({ files, onFileRemove }) => {
    return files.length ? (
        <div className={styles['attached-files']}>
            {files.map((fileEntry) => (
                <FileTag
                    key={fileEntry.name}
                    file={fileEntry}
                    onFileRemove={onFileRemove}
                ></FileTag>
            ))}
        </div>
    ) : null;
};
