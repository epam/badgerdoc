import React, { useState, FC, useMemo } from 'react';

import { useArrayDataSource } from '@epam/uui';
import { SearchInput, PickerList, Spinner, Text } from '@epam/loveship';

import { Label, PagedResponse, Category } from 'api/typings';

import { useNotifications } from 'shared/components/notifications';
import { getError } from 'shared/helpers/get-error';

import styles from './task-sidebar-labels.module.scss';
import { useDocumentCategoriesByJob } from 'api/hooks/categories';

type TaskSidebarLabelsViewProps = {
    labels?: PagedResponse<Category>;
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
    jobId?: number;
    onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
    selectedLabels: Label[];
};

export const TaskSidebarLabels = ({
    jobId,
    onLabelsSelected,
    selectedLabels = []
}: TaskSidebarLabelsProps) => {
    const latestLabelsId = selectedLabels.map((label) => label.id);
    const [searchText, setSearchText] = useState('');
    const [pickerValue, setPickerValue] = useState<string[]>(latestLabelsId);

    const { notifyError } = useNotifications();

    const { data: labels, isError, isLoading } = useDocumentCategoriesByJob({ searchText, jobId });

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
