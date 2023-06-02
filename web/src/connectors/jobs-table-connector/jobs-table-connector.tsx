import { Button, DataTable, Panel } from '@epam/loveship';
import React, { FC, useEffect, useMemo, useRef, useState } from 'react';
import { useLazyDataSource } from '@epam/uui';
import { useAsyncSourceTable } from 'shared/hooks/async-source-table';
import { PagingCache, SortingDirection } from 'api/typings';
import JobPopup from 'pages/jobs/job-popup';
import { jobPropFetcher, useJobs } from 'api/hooks/jobs';
import { TableWrapper, usePageTable } from 'shared';
//TODO: move out styles from the connector
import styles from './jobs-table-connector.module.scss';
import { jobColumns } from './jobs-columns';
import { Job } from 'api/typings/jobs';
import {
    useColumnPickerFilter,
    useDateRangeFilter
} from '../../shared/components/filters/column-picker';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';
import {
    getFiltersFromStorage,
    prepareFiltersToSet,
    saveFiltersToStorage
} from '../../shared/helpers/set-filters';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';

type JobsTableConnectorProps = {
    onAddJob: () => void;
    onRowClick: (id: number) => void;
};
export const JobsTableConnector: FC<JobsTableConnectorProps> = ({ onAddJob, onRowClick }) => {
    const [shownPopup, shownPopupChange] = useState<'extraction' | 'annotation' | null>(null);
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
    } = usePageTable<Job>('creation_datetime');
    const { page, pageSize } = pageConfig;

    const { data, isFetching } = useJobs(
        {
            page,
            size: pageSize,
            searchText,
            sortConfig,
            filters
        },
        { cacheTime: 0 }
    );

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    useEffect(() => {
        const localFilters = getFiltersFromStorage('jobs');
        if (localFilters) setFilters(localFilters);
    }, []);

    useEffect(() => {
        if (tableValue.filter) {
            const filtersToSet = prepareFiltersToSet<Job, unknown>(tableValue);
            saveFiltersToStorage(filtersToSet, 'jobs');

            setFilters(filtersToSet);
        }
    }, [tableValue.filter]);

    const { dataSource } = useAsyncSourceTable<Job, number>(
        isFetching,
        data?.data ?? [],
        page,
        pageSize,
        searchText,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        }),
        sortBy: (job, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof Job,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    const namesCache = useRef<PagingCache<string>>({
        page: -1,
        cache: [],
        search: ''
    });

    const typesCache = useRef<PagingCache<string>>({
        page: -1,
        cache: [],
        search: ''
    });

    const statusesCache = useRef<PagingCache<string>>({
        page: -1,
        cache: [],
        search: ''
    });

    const loadJobNames = createPagingCachedLoader<string, string>(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await jobPropFetcher('name', pageNumber, pageSize, keyword)
    );

    const loadJobTypes = createPagingCachedLoader<string, string>(
        typesCache,
        async (pageNumber, pageSize, keyword) =>
            await jobPropFetcher('type', pageNumber, pageSize, keyword)
    );

    const loadJobStatuses = createPagingCachedLoader<string, string>(
        statusesCache,
        async (pageNumber, pageSize, keyword) =>
            await jobPropFetcher('status', pageNumber, pageSize, keyword)
    );

    const jobNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadJobNames,
            getId: (name) => name
        },
        []
    );

    const jobTypes = useLazyDataSource<string, string, unknown>(
        {
            api: loadJobTypes,
            getId: (type) => type
        },
        []
    );

    const jobStatuses = useLazyDataSource<string, string, unknown>(
        {
            api: loadJobStatuses,
            getId: (type) => type
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, 'name'>(
        jobNames,
        'name',
        { showSearch: true }
    );

    const renderTypeFilter = useColumnPickerFilter<string, string, unknown, 'type'>(
        jobTypes,
        'type',
        { showSearch: true }
    );

    const renderStatusFilter = useColumnPickerFilter<string, string, unknown, 'status'>(
        jobStatuses,
        'status',
        { showSearch: true }
    );

    const renderDeadlineFilter = useDateRangeFilter('deadline');

    const renderCreationDateFilter = useDateRangeFilter('creation_datetime');

    const columns = useMemo(() => {
        const typeColumn = jobColumns.find(({ key }) => key === 'type');
        typeColumn!.isFilterActive = (filter) =>
            (filter.type && filter.type.in && Boolean(filter.type.in.length)) ?? false;
        typeColumn!.renderFilter = renderTypeFilter;

        const nameColumn = jobColumns.find(({ key }) => key === 'name');
        nameColumn!.isFilterActive = (filter) =>
            (filter.name && filter.name.in && Boolean(filter.name.in.length)) ?? false;
        nameColumn!.renderFilter = renderNameFilter;

        const statusColumn = jobColumns.find(({ key }) => key === 'status');
        statusColumn!.isFilterActive = (filter) =>
            (filter.status && filter.status.in && Boolean(filter.status.in.length)) ?? false;
        statusColumn!.renderFilter = renderStatusFilter;

        const deadlineColumn = jobColumns.find(({ key }) => key === 'deadline');
        deadlineColumn!.renderFilter = renderDeadlineFilter;

        const creationDateColumn = jobColumns.find(({ key }) => key === 'creation_datetime');
        creationDateColumn!.renderFilter = renderCreationDateFilter;

        return jobColumns;
    }, [
        jobColumns,
        renderTypeFilter,
        renderNameFilter,
        renderStatusFilter,
        renderDeadlineFilter,
        renderCreationDateFilter
    ]);

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <div className={`${styles['title']} flex justify-between align-vert-center`}>
                <BreadcrumbNavigation breadcrumbs={[{ name: 'Extractions' }]} />
                <Button onClick={onAddJob} caption="Add Extraction" />
            </div>

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

            {shownPopup ? (
                <JobPopup popupType={shownPopup} closePopup={() => shownPopupChange(null)} />
            ) : null}
        </Panel>
    );
};
