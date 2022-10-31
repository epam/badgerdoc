import React, { FC, useCallback } from 'react';
import { Blocker } from '@epam/loveship';

import { UploadForm, AttachedFiles } from 'components';

type UploadFilesControlProps = {
    value: File[];
    onValueChange: (newValue: File[]) => void;
    isLoading: boolean;
};

export const UploadFilesControl: FC<UploadFilesControlProps> = ({
    value,
    onValueChange,
    isLoading
}) => {
    const onFilesAdded = useCallback(
        (files: Array<File>) => {
            const newValue = new Set(value);
            for (const file of files) {
                if (!newValue.has(file)) {
                    newValue.add(file);
                }
            }
            onValueChange(Array.from(newValue));
        },
        [value]
    );

    const onFileRemove = useCallback(
        (file: File) => {
            const newValue = new Set(value);
            newValue.delete(file);
            onValueChange(Array.from(newValue));
        },
        [value]
    );

    return (
        <div
            className="form-wrapper"
            style={{ padding: 0, display: 'flex', flexDirection: 'column' }}
        >
            <UploadForm onFilesAdded={onFilesAdded}></UploadForm>
            <AttachedFiles files={value} onFileRemove={onFileRemove} />
            {isLoading && <Blocker isEnabled={isLoading} />}
        </div>
    );
};
