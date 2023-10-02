// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useEffect } from 'react';
import { Button, DataTable, Panel } from '@epam/loveship';

import { Category, QueryHookParamsType, SortingDirection } from '../../api/typings';
import { TableWrapper, usePageTable } from '../../shared';
import { useArrayDataSource, useUuiContext } from '@epam/uui';
import { categoryColumns } from './categories-column';
import { useCategories } from '../../api/hooks/categories';
import styles from './categories-table-connector.module.scss';
import { ModalWithDisabledClickOutsideAndCross } from '../categories-modal-connector/categories-modal-connector';
import { TaskValidationValues } from '../categories-modal-connector/types';
import { ML_MENU_ITEMS } from '../../shared/contexts/current-user';
import { MultiSwitchMenu } from '../../shared/components/multi-switch-menu/MultiSwitchMenu';
import { useHistory } from 'react-router-dom';

type CategoriesTableConnectorProps = {};
export const CategoriesTableConnector: FC<CategoriesTableConnectorProps> = () => {
    const {
        tableValue,
        onTableValueChange,
        onPageChange,
        onTotalCountChange,
        totalCount,
        searchText,
        pageConfig,
        sortConfig,
        setSortConfig
    } = usePageTable<Category>('name');
    const { page, pageSize } = pageConfig;
    const { data } = useCategories(
        { page, size: pageSize, searchText, sortConfig } as QueryHookParamsType<Category>,
        {}
    );

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    const categoriesSource = useArrayDataSource<Category, number, unknown>(
        {
            items: data?.data ?? []
        },
        [data?.data]
    );

    //@ts-ignore
    const view = categoriesSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: (item) => {
                return uuiModals.show<TaskValidationValues>((props) => (
                    <ModalWithDisabledClickOutsideAndCross categoryValue={item.value} {...props} />
                ));
            }
        }),
        sortBy: (Category, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof Category,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    const { uuiModals } = useUuiContext();

    const history = useHistory();

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <div className={`${styles['title']} flex justify-between align-vert-center`}>
                <MultiSwitchMenu items={ML_MENU_ITEMS} currentPath={history.location.pathname} />
                <Button
                    onClick={() =>
                        uuiModals.show((props) => (
                            <ModalWithDisabledClickOutsideAndCross {...props} />
                        ))
                    }
                    caption="Add Category"
                />
            </div>
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
                    columns={categoryColumns}
                    headerTextCase="upper"
                />
            </TableWrapper>
        </Panel>
    );
};
