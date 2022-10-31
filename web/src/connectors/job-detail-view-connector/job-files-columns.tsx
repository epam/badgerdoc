import { FileDocument } from '../../api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

export default [
    {
        key: 'original_name',
        caption: 'File name',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.original_name} </Text>;
        },
        isSortable: true,
        grow: 2,
        shrink: 1
    },
    {
        key: 'status',
        caption: 'status',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.status} </Text>;
        },
        isSortable: true,
        grow: 1,
        shrink: 1
    },
    {
        key: 'pages',
        caption: 'Pages',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.pages} </Text>;
        },
        isSortable: false,
        grow: 1,
        shrink: 1
    }
];
