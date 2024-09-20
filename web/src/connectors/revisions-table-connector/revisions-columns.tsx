// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, @typescript-eslint/no-unused-vars */
import { DataColumnProps } from '@epam/uui';
import { Revision } from 'api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

export const revisionsColumns: DataColumnProps<Revision>[] = [
    {
        key: 'revision',
        caption: 'REVISION ID',
        render: (file) => <Text>{file.revision}</Text>,
        grow: 1,
        minWidth: 100,
        isSortable: true,
        width: 150
    },
    {
        key: 'date',
        caption: 'CREATED DATE',
        render: (file) => <Text>{new Date(file.date).toLocaleDateString()}</Text>,
        grow: 0,
        minWidth: 100,
        isSortable: true,
        width: 150
    }
];
