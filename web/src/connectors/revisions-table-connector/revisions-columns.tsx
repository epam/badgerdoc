// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, @typescript-eslint/no-unused-vars */
import { DataColumnProps } from '@epam/uui';
import { Revision } from 'api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

export const revisionsColumns: DataColumnProps<Revision>[] = [
    {
        key: 'name',
        caption: 'REVISION ID',
        render: (file) => <Text>{file.name}</Text>,
        grow: 1,
        minWidth: 100,
        isSortable: true,
        width: 150
    },
    {
        key: 'created',
        caption: 'CREATED DATE',
        render: (file) => <Text>{new Date(file.created).toLocaleDateString()}</Text>,
        grow: 0,
        minWidth: 100,
        isSortable: true,
        width: 150
    }
];
