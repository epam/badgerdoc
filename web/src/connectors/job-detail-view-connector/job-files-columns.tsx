// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, @typescript-eslint/no-unused-vars */
import { FileDocument } from '../../api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

// eslint-disable-next-line import/no-anonymous-default-export
export default [
    {
        key: 'original_name',
        caption: 'File name',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.original_name} </Text>;
        },
        isSortable: true,
        grow: 2,
        shrink: 1,
        width: 100
    },
    {
        key: 'status',
        caption: 'status',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.status} </Text>;
        },
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'pages',
        caption: 'Pages',
        render: (file: FileDocument) => {
            return <Text key={file.id}> {file.pages} </Text>;
        },
        isSortable: false,
        grow: 1,
        shrink: 1,
        width: 100
    }
];
