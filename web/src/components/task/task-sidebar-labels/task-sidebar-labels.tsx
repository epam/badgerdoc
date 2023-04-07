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
    categories?: Category[];
    pickerValue: Label[];
    onValueChange: (value: Label[]) => void;
    hasNextPage: boolean;
    onFetchNext: () => void;
    isLoading: boolean;
};

const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    viewMode = false,
    categories,
    pickerValue,
    onValueChange,
    hasNextPage,
    onFetchNext,
    isLoading
}) => {
    const bottomLineRef = useRef(null);
    const containerRef = useRef(null);

    const { task } = useTaskAnnotatorContext();
    const isDisabled = task?.status !== 'In Progress' && task?.status !== 'Ready';

    if (!categories) {
        return <Spinner color="sky" />;
    }

    const labels = useMemo(() => categories.map(({ name, id }) => ({ name, id })), [categories]);
    const pickedIds = useMemo(() => pickerValue.map(({ id }) => id), [pickerValue]);

    const dataSource = useArrayDataSource<Label, string, unknown>({ items: labels }, [labels]);

    useLazyLoading(bottomLineRef, containerRef, onFetchNext);

    const renderData =
        viewMode || isDisabled ? (
            <FlexCell width="auto" style={{ overflow: 'hidden' }}>
                {labels.map(({ id, name }) => (
                    <Checkbox
                        cx={styles.checkbox}
                        label={name}
                        key={id}
                        value={pickedIds.includes(name)}
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
                    onValueChange={(value) => onValueChange(value ?? [])}
                    entityName="location"
                    selectionMode="multi"
                    valueType="entity"
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
    categories?: Category[];
    onLabelsSelected: (value: Label[]) => void;
    selectedLabels: Label[];
    searchText: string;
    setSearchText: (text: string) => void;
    hasNextPage: boolean;
    onFetchNext: () => void;
    isLoading: boolean;
};

export const TaskSidebarLabels = ({
    viewMode = false,
    categories,
    onLabelsSelected,
    selectedLabels = [],
    searchText,
    setSearchText,
    hasNextPage,
    onFetchNext,
    isLoading
}: TaskSidebarLabelsProps) => {
    const [pickerValue, setPickerValue] = useState(selectedLabels);

    const handleOnValueChange = (value: Label[]) => {
        setPickerValue(value);
        onLabelsSelected(value);
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
            {categories ? (
                <TaskSidebarLabelsView
                    viewMode={viewMode}
                    categories={categories}
                    isLoading={isLoading}
                    hasNextPage={hasNextPage}
                    onFetchNext={onFetchNext}
                    pickerValue={pickerValue}
                    onValueChange={handleOnValueChange}
                />
            ) : (
                <Spinner color="sky" />
            )}
        </div>
    );
};
