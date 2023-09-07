import React, { FC, useContext, useEffect, useMemo } from 'react';
import { DataTable, Panel, Text } from '@epam/loveship';
import { TableWrapper, usePageTable } from 'shared';
import { useTaskForDashboard } from 'api/hooks/tasks';
import { Task, TaskStatus } from 'api/typings/tasks';
import { useColumns } from './sh-columns';
import { CurrentUser } from '../../shared/contexts/current-user';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Operators, SortingDirection, TableFilters, ValidationType } from 'api/typings';
import { DataSourceState, IDataSourceView } from '@epam/uui';
import { JobVariables, addJob } from '../../api/hooks/jobs';

import { useNotifications } from 'shared/components/notifications';
import { getError } from '../../shared/helpers/get-error';

type SHDashboardTableConnectorProps = {
    onRowClick: (id: number) => void;
    filesIds: any;
    onJobAdded(): void;
};

export const SHDashboardTableConnector: FC<SHDashboardTableConnectorProps> = ({
    onRowClick,
    filesIds,
    onJobAdded
}) => {
    const { notifyError, notifySuccess } = useNotifications();
    const { currentUser } = useContext(CurrentUser);

    const columns = useColumns();

    const {
        view,
        tableValue,
        onTableValueChange,
        page,
        pageSize,
        totalCount,
        onPageChange,
        refetch
    } = useView({
        onRowClick
    });

    if (filesIds?.response && currentUser?.id) {
        const initialValues: JobVariables = {
            files: filesIds.response as string[],
            name: `${currentUser?.id} - SkillHunterJob`,
            datasets: [],
            pipeline_name: 'dod table table-post v0.2',
            type: 'ExtractionWithAnnotationJob',
            deadline: '2022-03-10T10:00:35.605Z',
            is_auto_distribution: true,
            is_draft: false,
            categories: [],
            validation_type: ValidationType.validationOnly,
            owners: [currentUser.id],
            annotators: [],
            validators: [currentUser.id]
        };
        try {
            addJob(initialValues);
            notifySuccess(<Text> Job created successfully. Job will be started soon </Text>);
            refetch();
        } catch (err) {
            notifyError(<Text> Job creation failed :{getError(err)}</Text>);
        }

        onJobAdded();
    }

    return (
        <>
            <Panel
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': columns.length
                }}
            >
                <TableWrapper
                    page={page}
                    pageSize={pageSize}
                    totalCount={totalCount}
                    onPageChange={onPageChange}
                >
                    <DataTable
                        {...view.getListProps()}
                        getRows={view.getVisibleRows}
                        value={tableValue}
                        onValueChange={onTableValueChange}
                        columns={columns}
                        headerTextCase="upper"
                    />
                </TableWrapper>
            </Panel>
        </>
    );
};

type UseViewProps = {
    onRowClick: (id: number) => void;
};

type UseViewOutput<DataSourceType> = {
    view: IDataSourceView<Task, number, any>;
    tableValue: DataSourceState<TableFilters<DataSourceType, TaskStatus[] | boolean[]>, any>;
    onTableValueChange: (data: DataSourceState<TableFilters<DataSourceType, []>, any>) => void;
    page: number;
    pageSize: number;
    totalCount: number;
    searchText: string;
    setSearchText: (text: string) => void;
    onPageChange: (page: number, pageSize?: number | undefined) => void;
    refetch: () => void;
};

const useView = ({ onRowClick }: UseViewProps): UseViewOutput<Task> => {
    const {
        pageConfig,
        onPageChange,
        totalCount,
        onTotalCountChange,
        searchText,
        setSearchText,
        tableValue,
        onTableValueChange,
        sortConfig,
        setSortConfig,
        setFilters,
        filters
    } = usePageTable<Task, TableFilters<Task, TaskStatus[] | boolean[]>>('id');
    const { page, pageSize } = pageConfig;
    const { currentUser } = useContext(CurrentUser);

    const { data, isFetching, refetch } = useTaskForDashboard(
        { user_id: currentUser?.id, page, size: pageSize, sortConfig, filters },
        {
            cacheTime: 0
        }
    );

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    useEffect(() => {
        onTableValueChange({
            ...tableValue,
            filter: {
                status: { [Operators.IN]: ['Ready', 'In Progress', 'Pending'] },
                is_validation: { [Operators.IN]: [true, false] }
            }
        });

        return () => {
            dataSource.unsubscribeView(onTableValueChange);
        };
    }, []);

    useEffect(() => {
        if (tableValue.sorting && tableValue.sorting.length) {
            let { field, direction } = tableValue.sorting[0];
            if (field !== sortConfig.field || direction !== sortConfig.direction) {
                setSortConfig({
                    field: field as keyof Task,
                    direction: direction as SortingDirection
                });
            }
        }

        if (tableValue.filter) {
            const filters = Object.keys(tableValue.filter);
            const filtersToSet = filters.map((item) => {
                const field = item as keyof Task;
                const operator = Object.keys(
                    tableValue.filter![field as keyof Task]!
                )[0] as Operators;
                const value = tableValue.filter![field]![operator]!;
                return { field, operator, value };
            });
            setFilters(filtersToSet);
        }
    }, [tableValue.filter, tableValue.sorting, sortConfig]);

    const { dataSource } = useAsyncSourceTable<Task, number>(
        isFetching,
        data?.data ?? [],
        page,
        pageSize,
        currentUser?.id,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        })
    });

    return useMemo(
        () => ({
            view,
            tableValue,
            onTableValueChange,
            page,
            pageSize,
            totalCount,
            searchText,
            setSearchText,
            onPageChange,
            refetch
        }),
        [data, view, tableValue, searchText]
    );
};
