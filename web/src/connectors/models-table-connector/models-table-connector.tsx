// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import { Button, DataTable, Panel } from '@epam/loveship';
import React, { FC, useEffect, useMemo } from 'react';
import { Model, Operators, SortingDirection, TableFilters } from 'api/typings';

import { TableWrapper, usePageTable } from 'shared';
import { modelsColumns } from './models-columns';
import { useModels } from '../../api/hooks/models';
import ModelPanel from '../../components/model/model-panel';
import { useArrayDataSource } from '@epam/uui';
import { ModelStatus, ModelType } from 'api/typings/models';
import { useColumnPickerFilter } from 'shared/components/filters/column-picker';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { useBasements } from 'api/hooks/basements';
import { useUsers } from 'api/hooks/users';
import { useTableColumns } from '../../shared/hooks/table-columns';
import styles from './models-table-connector.module.scss';
import { MultiSwitchMenu } from '../../shared/components/multi-switch-menu/MultiSwitchMenu';
import { useHistory } from 'react-router-dom';
import { ML_MENU_ITEMS } from '../../shared/contexts/current-user';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
type JobsTableConnectorProps = {
    onAddModel: () => void;
    onRowClick: (id: string, version?: number) => void;
};
export const ModelsTableConnector: FC<JobsTableConnectorProps> = ({ onAddModel, onRowClick }) => {
    const {
        pageConfig,
        onPageChange,
        totalCount,
        onTotalCountChange,
        searchText,
        tableValue,
        onTableValueChange,
        sortConfig,
        setSortConfig,
        setFilters,
        filters
    } = usePageTable<Model, TableFilters<Model, ModelStatus[] | ModelType[]>>('name');
    const { page, pageSize } = pageConfig;

    const { data: basements } = useBasements(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const { data: users } = useUsers(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'username', direction: SortingDirection.ASC }
        },
        {}
    );

    const statusesDS = useArrayDataSource<ModelStatus, string, unknown>(
        {
            items: ['deployed', 'ready', 'failed', 'deploying'],
            getId: (status) => status
        },
        []
    );

    const typesDS = useArrayDataSource<ModelType, string, unknown>(
        {
            items: [
                'Molecule',
                'Table',
                'Dod',
                'Graphic',
                'preprocessing',
                'Illustration',
                'Ternary',
                'Handwriting'
            ],
            getId: (type) => type
        },
        []
    );

    const basementsDS = useArrayDataSource<string, string, unknown>(
        {
            items: basements?.data.map((el) => el.id) || [],
            getId: (basement) => basement
        },
        []
    );

    const usersDS = useArrayDataSource<string, string, unknown>(
        {
            items: users?.data.map((el) => el.username) || [],
            getId: (user) => user
        },
        []
    );

    const renderBasementFilter = useColumnPickerFilter<string, string, unknown, 'basement'>(
        basementsDS,
        'basement'
    );

    const renderStatusFilter = useColumnPickerFilter<ModelStatus, string, unknown, 'status'>(
        statusesDS,
        'status'
    );

    const renderTypeFilter = useColumnPickerFilter<ModelType, string, unknown, 'type'>(
        typesDS,
        'type'
    );

    const renderAuthorFilter = useColumnPickerFilter<string, string, unknown, 'created_by'>(
        usersDS,
        'created_by'
    );

    const columns = useTableColumns(modelsColumns, [
        {
            key: 'status',
            render: renderStatusFilter
        },
        {
            key: 'type',
            render: renderTypeFilter
        },
        {
            key: 'basement',
            render: renderBasementFilter
        },
        {
            key: 'created_by',
            render: renderAuthorFilter
        }
    ]);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('models');
        if (localFilters) setFilters(localFilters);
        else
            onTableValueChange({
                ...tableValue,
                filter: {
                    status: { [Operators.IN]: ['ready', 'deployed'] }
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
                    field: field as keyof Model,
                    direction: direction as SortingDirection
                });
            }
        }

        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Model, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'models');

            setFilters(filtersToSet);
        }
    }, [tableValue.filter, tableValue.sorting, sortConfig]);

    const { data, isFetching } = useModels(
        { page, size: pageSize, searchText, sortConfig, filters },
        {
            cacheTime: 0
        }
    );
    const acc: Model[] | undefined = useMemo(() => {
        return (
            data?.data &&
            data.data
                .map((curr: Model) => {
                    return [
                        {
                            ...curr,
                            name: `${curr.name} v${curr.version}${curr.latest ? '-latest' : ''}`,
                            id: `${curr.name}-${curr.version}`,
                            parentId: curr.id
                        } as Model,
                        {
                            id: curr.id,
                            name: curr.name
                        } as Model
                    ];
                })
                .flat()
                .filter(
                    (value, index, self) =>
                        index === self.findIndex((t) => t.id === value.id && t.name === value.name)
                )
        );
    }, [data?.data]);

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    const { dataSource } = useAsyncSourceTable<Model, number>(
        isFetching,
        acc ?? [],
        page,
        pageSize,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            onClick: (item) => {
                if (item.value?.version)
                    return onRowClick(
                        item.path?.[0] ? item.path?.[0].id.toString() : item.id.toString(),
                        item.value?.version
                    );
                return item;
            }
        })
    });

    const history = useHistory();

    return (
        <ModelPanel>
            <div className={`flex justify-between align-vert-center ${styles.title}`}>
                <MultiSwitchMenu items={ML_MENU_ITEMS} currentPath={history.location.pathname} />
                <Button onClick={onAddModel} caption="Add Model" />
            </div>

            <Panel
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': modelsColumns.length
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
        </ModelPanel>
    );
};
