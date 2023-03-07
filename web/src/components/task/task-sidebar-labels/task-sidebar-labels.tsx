import React, { useState } from 'react';

import { SearchInput, Spinner } from '@epam/loveship';

import { Label, Category } from 'api/typings';
import { TaskSidebarLabelsView } from '../task-sidebar-labels-view';

import styles from './task-sidebar-labels.module.scss';

type TaskSidebarLabelsProps = {
    viewMode: boolean;
    labels?: Category[];
    onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
    selectedLabels: Label[];
    searchText: string;
    setSearchText: (text: string) => void;
};

export const TaskSidebarLabels = ({
    viewMode = false,
    labels,
    onLabelsSelected,
    selectedLabels = [],
    searchText,
    setSearchText
}: TaskSidebarLabelsProps) => {
    const latestLabelsId = selectedLabels.map((label) => label.id);
    const [pickerValue, setPickerValue] = useState<string[]>(latestLabelsId);

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
            {labels ? (
                <TaskSidebarLabelsView
                    viewMode={viewMode}
                    labels={labels}
                    pickerValue={pickerValue}
                    onValueChange={handleOnValueChange}
                    selectedLabels={selectedLabels}
                />
            ) : (
                <Spinner color="sky" />
            )}
        </div>
    );
};
