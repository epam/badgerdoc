import { Button, DataTable, Panel } from '@epam/loveship';
import React, { FC, useEffect } from 'react';
import { Basement, Operators, SortingDirection, TableFilters } from 'api/typings';

import { TableWrapper, usePageTable } from 'shared';
import { basementColumns } from './basements-columns';
import ModelPanel from '../../components/model/model-panel';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { useBasements } from 'api/hooks/basements';
import { useTableColumns } from '../../shared/hooks/table-columns';
import styles from './basements-table-connector.module.scss';
import BasementPopup from '../../components/basement/basement-popup/basement-popup';
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
    onRowClick: (id?: Basement) => void;
    popup: {
        show: boolean;
        basement?: Basement;
    };
    onPopupClose: () => void;
};
export const BasementsTableConnector: FC<JobsTableConnectorProps> = ({
    onAddModel,
    onRowClick,
    popup,
    onPopupClose
}) => {
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
    } = usePageTable<Basement, TableFilters<Basement, null>>('name');
    const { page, pageSize } = pageConfig;

    const columns = useTableColumns(basementColumns, []);

    useEffect(() => {
        onTableValueChange({
            ...tableValue,
            filter: {}
        });

        return () => {
            dataSource.unsubscribeView(onTableValueChange);
        };
    }, []);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('basements');
        if (localFilters) setFilters(localFilters);
    }, []);

    useEffect(() => {
        if (tableValue.sorting && tableValue.sorting.length) {
            let { field, direction } = tableValue.sorting[0];
            if (field !== sortConfig.field || direction !== sortConfig.direction) {
                setSortConfig({
                    field: field as keyof Basement,
                    direction: direction as SortingDirection
                });
            }
        }

        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Basement, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'basements');
            setFilters(filtersToSet);
        }
    }, [tableValue.filter, tableValue.sorting, sortConfig]);

    const { data, isFetching } = useBasements(
        { page, size: pageSize, searchText, sortConfig, filters },
        {
            cacheTime: 0
        }
    );

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    const { dataSource } = useAsyncSourceTable<Basement, number>(
        isFetching,
        data?.data ?? [],
        page,
        pageSize,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: ({ id }) => {
                const item = data?.data.find((el) => el.id === id.toString());
                onRowClick(item);
            }
        })
    });

    const history = useHistory();

    return (
        <ModelPanel>
            <div className={`flex justify-between align-vert-center ${styles.title}`}>
                <MultiSwitchMenu items={ML_MENU_ITEMS} currentPath={history.location.pathname} />
                <Button onClick={onAddModel} caption="Add Basement" />
            </div>

            <Panel
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': basementColumns.length
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
            {popup.show ? <BasementPopup basement={popup.basement} onClose={onPopupClose} /> : null}
        </ModelPanel>
    );
};
