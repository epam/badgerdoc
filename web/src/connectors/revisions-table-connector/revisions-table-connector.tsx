// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import { DataTable } from '@epam/loveship';
import React, { FC, useEffect, useMemo, useState } from 'react';
import { useArrayDataSource } from '@epam/uui';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { Revision, SortingDirection } from 'api/typings';
import { pageSizes, TableWrapper, usePageTable } from 'shared';
import { revisionsColumns } from './revisions-columns';
import {
    useColumnPickerFilter,
    useDateRangeFilter
} from '../../shared/components/filters/column-picker';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
import { useRevisions } from 'api/hooks/revisions';

//TODO: move out styles from the connector
import styles from './revisions-table-connector.module.scss';

type RevisionsTableConnectorProps = {
    onRowClick: (id: number | string) => void;
    onRevisionSelect?: (revision: string[]) => void;
    checkedValues?: string[];
};
const size = pageSizes._100;

export const RevisionsTableConnector: FC<RevisionsTableConnectorProps> = ({
    onRowClick,
    onRevisionSelect,
    checkedValues
}) => {
    const [selectedRevisions, setSelectedRevisions] = useState<string[] | []>([]);
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
    } = usePageTable<Revision>('date');
    const { page, pageSize } = pageConfig;
    const { checked } = tableValue;

    const { data, isFetching, refetch } = useRevisions(
        { searchText, sortConfig, page, size, filters },
        { cacheTime: 0 }
    );

    useEffect(() => {
        if (checkedValues) {
            onTableValueChange({
                ...tableValue,
                checked: checkedValues
            });
        }
    }, []);

    useEffect(() => {
        setSelectedRevisions(checked || []);
        if (onRevisionSelect) {
            onRevisionSelect(checked as string[]);
        }
    }, [checked]);

    useEffect(() => {
        if (onRevisionSelect) {
            onRevisionSelect(selectedRevisions as string[]);
        }
    }, [selectedRevisions]);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('revisions');
        if (localFilters) setFilters(localFilters);
    }, []);

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    useEffect(() => {
        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Revision, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'revisions');

            setFilters(filtersToSet);
        }
    }, [tableValue.filter]);

    useEffect(() => {
        refetch();
    }, [filters]);

    const transformedData = useMemo(() => {
        return (
            data?.data &&
            data.data
                .map((revision) => {
                    return [
                        {
                            ...revision,
                            id: revision.revision
                        }
                    ];
                })
                .flat()
        );
    }, [data?.data]);

    const { dataSource } = useAsyncSourceTable<Revision, number>(
        isFetching,
        transformedData ?? [],
        page,
        pageSize,
        searchText,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            checkbox: { isVisible: true },
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        }),
        sortBy: (revision, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof Revision,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    useEffect(() => () => dataSource.unsubscribeView(onTableValueChange), []);

    const revisions = useMemo(() => {
        return data?.data
            ? data.data.map((revision) => {
                  return revision.revision;
              })
            : [];
    }, [data?.data]);

    const revisionNames = useArrayDataSource<string, string, unknown>(
        {
            items: revisions,
            getId: (item) => item.toString()
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, 'revision'>(
        revisionNames,
        'revision',
        { showSearch: true, isPickByEntity: true }
    );

    const renderCreationDateFilter = useDateRangeFilter('date');

    const columns = useMemo(() => {
        const nameColumn = revisionsColumns.find(({ key }) => key === 'revision');
        nameColumn!.renderFilter = renderNameFilter;

        const createdDateColumn = revisionsColumns.find(({ key }) => key === 'date');
        createdDateColumn!.renderFilter = renderCreationDateFilter;

        return revisionsColumns;
    }, [revisionsColumns, renderNameFilter, renderCreationDateFilter]);

    return (
        <div className={styles.wrapper}>
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
        </div>
    );
};
