import React, { useState, FC, useEffect } from 'react';

import { useArrayDataSource } from '@epam/uui';
import { SearchInput, PickerList, Spinner, Text } from '@epam/loveship';

import { Filter, Operators, SortingDirection, Taxon, Label, PagedResponse } from 'api/typings';

import { useNotifications } from 'shared/components/notifications';
import { useTaxonomies } from 'api/hooks/taxonomies';
import { getError } from 'shared/helpers/get-error';

import { getTaxonsId } from 'shared/helpers/utils';
import styles from './task-sidebar-labels.module.scss';

type TaskSidebarLabelsViewProps = {
    labels: PagedResponse<Taxon> | undefined;
    pickerValue: string[];
    onValueChange: (e: any, labelsArr: Label[]) => void;
};

const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    labels,
    pickerValue,
    onValueChange
}) => {
    if (!labels) {
        return <Spinner color="sky" />;
    }

    const labelsArr = labels.data.map((el: { name: string; id: string }) => {
        return { name: el.name, id: el.id };
    });
    const dataSource = useArrayDataSource({ items: labelsArr }, [labels]);

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
    categories: any;
    onLabelsSelected: (labels: Label[]) => void;
    selectedLabels: Label[];
};

export const TaskSidebarLabels = ({
    categories,
    onLabelsSelected,
    selectedLabels = []
}: TaskSidebarLabelsProps) => {
    const latestLabelsId = selectedLabels.map((label) => label.id);
    const [searchText, setSearchText] = useState('');
    const [pickerValue, setPickerValue] = useState<string[]>(latestLabelsId);

    const { notifyError } = useNotifications();
    const ids: string[] = getTaxonsId(categories);
    const taxonomyFilter: Filter<keyof Taxon> = {
        field: 'taxonomy_id',
        operator: ids.length > 1 ? Operators.IN : Operators.EQ,
        value: ids.length > 1 ? ids : ids[0]
    };

    const {
        data: labels,
        isLoading,
        isError,
        refetch
    } = useTaxonomies(
        {
            page: 1,
            size: 100,
            searchText,
            searchField: searchText ? 'taxonomy_id' : undefined,
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
        onLabelsSelected(selectedLabels);
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
                />
            )}
        </div>
    );
};
