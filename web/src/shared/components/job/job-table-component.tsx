// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import { DataTable } from '@epam/loveship';
import { TableWrapper } from '../table-wrapper';
import { DataColumnProps, DataSourceState, IDataSourceView } from '@epam/uui';
import { FileDocument, TableFilters } from '../../../api/typings';
import { ApiTask } from '../../../api/typings/tasks';

type JobTablePropsType = {
    page: number;
    size: number;
    view: IDataSourceView<FileDocument | ApiTask, any, any>;
    value: DataSourceState<TableFilters<ApiTask | FileDocument, []>, any>;
    onValueChange: (data: DataSourceState<TableFilters<ApiTask | FileDocument, []>, any>) => void;
    columns: DataColumnProps<ApiTask | FileDocument, any, any>[];
    totalCount: number;
    onPageChange: (page: number) => void;
};

export const JobTable = ({
    page,
    size,
    value,
    view,
    onValueChange,
    columns,
    totalCount,
    onPageChange
}: JobTablePropsType) => {
    return (
        <TableWrapper
            page={page}
            pageSize={size}
            totalCount={totalCount}
            onPageChange={onPageChange}
        >
            <DataTable
                {...view.getListProps()}
                getRows={view.getVisibleRows}
                value={value}
                onValueChange={onValueChange}
                columns={columns}
                headerTextCase="upper"
            />
        </TableWrapper>
    );
};
