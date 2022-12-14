import React, { useState, FC, useEffect, useMemo } from 'react';

import { useArrayDataSource } from '@epam/uui';
import { SearchInput, PickerList, Spinner, Text } from '@epam/loveship';

import { Filter, Operators, SortingDirection, Taxon, Label, PagedResponse } from 'api/typings';

import { useNotifications } from 'shared/components/notifications';
import { TaxonomyByJobIdResponse, useTaxons } from 'api/hooks/taxons';
import { getError } from 'shared/helpers/get-error';

import styles from './task-sidebar-labels.module.scss';

type TaskSidebarLabelsViewProps = {
    labels: PagedResponse<Taxon> | undefined;
    pickerValue: string[];
    onValueChange: (e: any, labelsArr: Label[]) => void;
    selectedLabels: Label[];
};

const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    labels,
    pickerValue,
    onValueChange,
    selectedLabels
}) => {
    if (!labels) {
        return <Spinner color="sky" />;
    }
    const labelsArr = useMemo(
        () =>
            labels.data.map((el: { name: string; id: string }) => {
                return { name: el.name, id: el.id };
            }),
        [labels]
    );

    const dataSource = useArrayDataSource({ items: [...selectedLabels, ...labelsArr] }, [labels]);

    return (
        <div className={`${styles.picker_list}`}>
            <PickerList<Label, Label | unknown>
                dataSource={dataSource}
                value={pickerValue}
                onValueChange={(e) => onValueChange(e ?? [], labelsArr)}
                entityName="location"
                selectionMode="multi"
                valueType="id"
                maxDefaultItems={100}
                maxTotalItems={100}
                sorting={{ field: 'name', direction: 'asc' }}
            />
        </div>
    );
};

type TaskSidebarLabelsProps = {
    taxonomies: TaxonomyByJobIdResponse | undefined;
    onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
    selectedLabels: Label[];
};

export const TaskSidebarLabels = ({
    taxonomies,
    onLabelsSelected,
    selectedLabels = []
}: TaskSidebarLabelsProps) => {
    const latestLabelsId = selectedLabels.map((label) => label.id);
    const [searchText, setSearchText] = useState('');
    const [pickerValue, setPickerValue] = useState<string[]>(latestLabelsId);

    const { notifyError } = useNotifications();

    const taxonomyIds = useMemo(() => taxonomies?.map((taxonomy) => taxonomy.id), [taxonomies]);

    const taxonomyFilter: Filter<keyof Taxon> = {
        field: 'taxonomy_id',
        operator: Operators.IN,
        value: taxonomyIds
    };

    const {
        data: labels,
        isLoading,
        isError,
        refetch
    } = useTaxons(
        {
            page: 1,
            size: 100,
            searchText,
            searchField: searchText ? 'name' : undefined,
            filters: [taxonomyFilter],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    useEffect(() => {
        if (searchText) {
            refetch();
        }
    }, [searchText]);

    if (isError) {
        notifyError(<Text>{getError(isError)}</Text>);
    }

    const handleOnValueChange = (e: string[], labelsArr: Label[]) => {
        const selectedLabels = labelsArr.filter((label) => {
            if (e.includes(label.id)) {
                return label;
            }
        });

        let labelsId: string[] = [];
        if (Array.isArray(e)) {
            labelsId = e;
        }
        setPickerValue(labelsId);
        onLabelsSelected(selectedLabels, labelsId);
    };

    return (
        <div className={`${styles.container}`}>
            <p className={`${styles.header}`}> Add labels for the entire document</p>
            <SearchInput
                value={searchText}
                onValueChange={(text) => setSearchText(text ? text : '')}
                debounceDelay={800}
                cx={styles.search}
                size="24"
                placeholder="Search by label name"
            />
            {isLoading && <Spinner color="sky" />}
            {!isLoading && !isError && (
                <TaskSidebarLabelsView
                    labels={labels}
                    pickerValue={pickerValue}
                    onValueChange={handleOnValueChange}
                    selectedLabels={selectedLabels}
                />
            )}
        </div>
    );
};
