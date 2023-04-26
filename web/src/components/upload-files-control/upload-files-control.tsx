import React, { FC, useCallback } from 'react';
import { Blocker } from '@epam/loveship';

import { UploadForm, AttachedFiles } from 'components';

type UploadFilesControlProps = {
    value: File[];
    isLoading: boolean;
    onValueChange: (value: File[]) => void;
};

export const UploadFilesControl: FC<UploadFilesControlProps> = ({
    value,
    isLoading,
    onValueChange
}) => {
    const onFilesAdded = useCallback(
        (files: Array<File>) => {
            const changedValue = [...value];
            const filesNames = new Set(value.map(({ name }) => name));

            for (const file of files) {
                if (!filesNames.has(file.name)) {
                    changedValue.push(file);
                }
            }

            onValueChange(changedValue);
        },
        [value]
    );

    const onFileRemove = useCallback(
        (file: File) => {
            onValueChange(value.filter((item) => item !== file));
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
