import React, { useState, FC, useMemo, useRef } from 'react';
import { noop } from 'lodash';

import { useArrayDataSource } from '@epam/uui';
import { SearchInput, PickerList, Spinner, Checkbox, FlexCell } from '@epam/loveship';

import { Label, Category } from 'api/typings';

import styles from './task-sidebar-labels.module.scss';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { useLazyLoading } from 'shared/hooks/lazy-loading';

type TaskSidebarLabelsViewProps = {
    viewMode: boolean;
    labels?: Category[];
    pickerValue: string[];
    onValueChange: (value: string[], labelsArr: Label[]) => void;
    selectedLabels: Label[];
    hasNextPage: boolean;
    onFetchNext: () => void;
    isLoading: boolean;
};

const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    viewMode = false,
    labels,
    pickerValue,
    onValueChange,
    selectedLabels,
    hasNextPage,
    onFetchNext,
    isLoading
}) => {
    const bottomLineRef = useRef(null);
    const containerRef = useRef(null);

    const { task } = useTaskAnnotatorContext();
    const isDisabled = task?.status !== 'In Progress' && task?.status !== 'Ready';

    if (!labels) {
        return <Spinner color="sky" />;
    }

    const labelsArr = useMemo(() => labels.map(({ name, id }) => ({ name, id })), [labels]);

    const dataSource = useArrayDataSource<Label, string, unknown>(
        { items: [...selectedLabels, ...labelsArr] },
        [labels]
    );

    useLazyLoading(bottomLineRef, containerRef, onFetchNext);

    const renderData =
        viewMode || isDisabled ? (
            <FlexCell width="auto" style={{ overflow: 'hidden' }}>
                {labelsArr.map(({ id, name }) => (
                    <Checkbox
                        cx={styles.checkbox}
                        label={name}
                        key={id}
                        value={pickerValue.includes(name)}
                        onValueChange={noop}
                        isDisabled={isDisabled}
                    />
                ))}
            </FlexCell>
        ) : (
            <>
                <PickerList<Label, string>
                    dataSource={dataSource}
                    value={pickerValue}
                    onValueChange={(value) => onValueChange(value ?? [], labelsArr)}
                    entityName="location"
                    selectionMode="multi"
                    valueType="id"
                    maxDefaultItems={100}
                    maxTotalItems={100}
                    sorting={{ field: 'name', direction: 'asc' }}
                />
            </>
        );

    return (
        <div ref={containerRef} className={`${styles.picker_list} ${viewMode && styles.disabled}`}>
            {renderData}
            {isLoading && <Spinner color="sky" />}
            {hasNextPage && <div ref={bottomLineRef} />}
        </div>
    );
};

type TaskSidebarLabelsProps = {
    viewMode: boolean;
    labels?: Category[];
    onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
    selectedLabels: Label[];
    searchText: string;
    setSearchText: (text: string) => void;
    hasNextPage: boolean;
    onFetchNext: () => void;
    isLoading: boolean;
};

export const TaskSidebarLabels = ({
    viewMode = false,
    labels,
    onLabelsSelected,
    selectedLabels = [],
    searchText,
    setSearchText,
    hasNextPage,
    onFetchNext,
    isLoading
}: TaskSidebarLabelsProps) => {
    const [pickerValue, setPickerValue] = useState(() => selectedLabels.map(({ id }) => id));

    const handleOnValueChange = (value: string[], labelsArr: Label[]) => {
        const selectedLabels = labelsArr.filter(({ id }) => value.includes(id));

        setPickerValue(value);
        onLabelsSelected(selectedLabels, value);
    };

    return (
        <div className={styles.container}>
            <p className={styles.header}> Add labels for the entire document</p>
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
                    isLoading={isLoading}
                    hasNextPage={hasNextPage}
                    onFetchNext={onFetchNext}
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
