import { DataColumnProps } from '@epam/uui';
import { FileDocument } from 'api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

export const documentColumns: DataColumnProps<FileDocument>[] = [
    {
        key: 'original_name',
        caption: 'DOCUMENT NAME',
        render: (file) => <Text>{file.original_name}</Text>,
        grow: 1,
        minWidth: 224,
        isSortable: true
    },
    {
        key: 'last_modified',
        caption: 'DATE',
        render: (file) => <Text>{new Date(file.last_modified).toLocaleDateString()}</Text>,
        grow: 0,
        minWidth: 100,
        isSortable: true
    },
    {
        key: 'size_in_bytes',
        caption: 'SIZE',
        render: (file) => {
            const sizeInKb = file.size_in_bytes / 1024;
            const sizeInMb = sizeInKb / 1024;
            const result = String(
                (sizeInMb > 1 ? sizeInMb : sizeInKb > 1 ? sizeInKb : file.size_in_bytes).toFixed(2)
            );
            const measurement = sizeInMb > 1 ? 'Mb' : sizeInKb > 1 ? 'Kb' : 'bytes';

            return (
                <Text>
                    {result} {measurement}
                </Text>
            );
        },
        grow: 0,
        minWidth: 100
    }
];
