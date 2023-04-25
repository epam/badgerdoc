import React, { FC, useEffect, useMemo, useRef } from 'react';
import {
    FilterWithDocumentExtraOption,
    Operators,
    PagingCache,
    SortingDirection,
    TableFilters
} from 'api/typings';
import { jobPropFetcher, useJobs } from 'api/hooks/jobs';
import { usePageTable } from 'shared';
import styles from './train-model-job.module.scss';
import { jobColumns } from './jobs-columns';
import { Job } from 'api/typings/jobs';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';
import { useColumnPickerFilter } from 'shared/components/filters/column-picker';
import { ModelValues } from '../model.models';

import { ILens, useArrayDataSource, useLazyDataSource } from '@epam/uui';
import { DataTable, Panel } from '@epam/loveship';

type JobsTableConnectorProps = {
    lens: ILens<ModelValues>;
};
export const TrainModelJob: FC<JobsTableConnectorProps> = ({ lens }) => {
    const {
        pageConfig,
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

    const { checked } = tableValue;

    useEffect(() => {
        const jobsArray = checked?.reduce((acc, el) => {
            const job = data?.data.find((elem) => elem.id === el);
            return [...acc, job];
        }, []);
        lens.prop('jobs').set(jobsArray);
    }, [checked]);

    const { data } = useJobs({ page, size: pageSize, searchText, sortConfig, filters }, {});

    useEffect(() => {
        if (data?.pagination.total !== undefined) {
            onTotalCountChange(data?.pagination.total);
        }
    }, [data?.pagination.total]);

    const jobsSource = useArrayDataSource<Job, number, TableFilters<Job, []>>(
        {
            items: data?.data ?? []
        },
        [data?.data]
    );

    useEffect(() => {
        if (tableValue.filter) {
            const filters = Object.keys(tableValue.filter);
            const filtersToSet = filters.flatMap((item) => {
                const field = item as keyof Job;
                const filter = tableValue.filter![field as keyof Job];
                const operator = Object.keys(
                    tableValue.filter![field as keyof Job]!
                )[0] as Operators;
                const operatorsArray = Object.keys(filter!);
                if (operatorsArray.length === 1) {
                    return {
                        field,
                        operator: operatorsArray[0] as Operators,
                        value: filter![operator]! as string[]
                    };
                } else if ('from' in filter! && 'to' in filter) {
                    return [
                        { field, operator: Operators.GE, value: filter['from'] },
                        { field, operator: Operators.LE, value: filter['to'] }
                    ];
                } else {
                    return null;
                }
            });
            setFilters(filtersToSet as (FilterWithDocumentExtraOption<keyof Job> | null)[]);
        }
    }, [tableValue.filter]);

    const namesCache = useRef<PagingCache<string>>({
        page: -1,
        cache: [],
        search: ''
    });

    const loadJobNames = createPagingCachedLoader<string, string>(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await jobPropFetcher('name', pageNumber, pageSize, keyword)
    );

    const jobNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadJobNames,
            getId: (name) => name
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, 'name'>(
        jobNames,
        'name',
        { showSearch: true }
    );

    const columns = useMemo(() => {
        const nameColumn = jobColumns.find(({ key }) => key === 'name');
        nameColumn!.renderFilter = renderNameFilter;

        return jobColumns;
    }, [jobColumns, renderNameFilter]);

    const view = jobsSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            checkbox: { isVisible: true },
            isSelectable: true
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

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <Panel
                rawProps={{
                    role: 'table',
                    'aria-rowcount': view.getListProps().rowsCount,
                    'aria-colcount': jobColumns.length
                }}
            >
                <DataTable
                    {...view.getListProps()}
                    getRows={view.getVisibleRows}
                    value={tableValue}
                    onValueChange={onTableValueChange}
                    columns={columns}
                    headerTextCase="upper"
                />
            </Panel>
        </Panel>
    );
};
export default TrainModelJob;
