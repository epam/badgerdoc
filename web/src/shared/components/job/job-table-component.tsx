import React from 'react';
import { DataTable } from '@epam/loveship';
import { TableWrapper } from '../table-wrapper';
import { DataColumnProps, DataSourceState, IDataSourceView } from '@epam/uui';
import { FileDocument, TableFilters } from '../../../api/typings';
import { Task } from '../../../api/typings/tasks';

type JobTablePropsType = {
    page: number;
    size: number;
    view: IDataSourceView<FileDocument | Task, any, any>;
    value: DataSourceState<TableFilters<Task | FileDocument, []>, any>;
    onValueChange: (data: DataSourceState<TableFilters<Task | FileDocument, []>, any>) => void;
    columns: DataColumnProps<Task | FileDocument, any, any>[];
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
