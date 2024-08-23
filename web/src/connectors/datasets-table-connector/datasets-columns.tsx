// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, @typescript-eslint/no-unused-vars */
import { DataColumnProps } from '@epam/uui';
import { Dataset } from 'api/typings';
import { Text } from '@epam/loveship';
import React from 'react';

export const datasetsColumns: DataColumnProps<Dataset>[] = [
    {
        key: 'name',
        caption: 'DATASET NAME',
        render: (file) => <Text>{file.name}</Text>,
        grow: 1,
        minWidth: 100,
        isSortable: true,
        width: 150
    },
    {
        key: 'count',
        caption: 'DOCUMENTS COUNT',
        render: (file) => <Text>{file.count}</Text>,
        grow: 1,
        minWidth: 100,
        isSortable: true,
        width: 100
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
