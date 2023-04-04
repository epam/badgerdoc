import React, { FC, useMemo, useRef } from 'react';
import { noop } from 'lodash';

import { useArrayDataSource } from '@epam/uui';
import { SearchInput, Spinner, Checkbox, FlexCell, PickerList } from '@epam/loveship';

import { Label, Category } from 'api/typings';

import styles from './task-sidebar-labels.module.scss';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { useLazyLoading } from 'shared/hooks/lazy-loading';

type TaskSidebarLabelsViewProps = {
    viewMode: boolean;
    categories?: Category[];
    onValueChange: (value: Label[]) => void;
    selectedLabels: Label[];
    hasNextPage: boolean;
    onFetchNext: () => void;
    isLoading: boolean;
};

const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    viewMode = false,
    categories,
    selectedLabels,
    onValueChange,
    hasNextPage,
    onFetchNext,
    isLoading
}) => {
    const bottomLineRef = useRef(null);
    const containerRef = useRef(null);

    useLazyLoading(bottomLineRef, containerRef, onFetchNext);

    const { task } = useTaskAnnotatorContext();
    const isDisabled = task?.status !== 'In Progress' && task?.status !== 'Ready';

    if (!categories) {
        return <Spinner color="sky" />;
    }

    const pickerLabelsIds = useMemo(
        () => selectedLabels.map((label) => label.id),
        [selectedLabels]
    );

    const labels = useMemo(() => categories.map(({ name, id }) => ({ name, id })), [categories]);

    const dataSource = useArrayDataSource<Label, string, unknown>(
        { items: [...selectedLabels, ...labels] },
        [labels]
    );

    const renderData =
        viewMode || isDisabled ? (
            <FlexCell width="auto" style={{ overflow: 'hidden' }}>
                {labels.map(({ id, name }) => (
                    <Checkbox
                        cx={styles.checkbox}
                        label={name}
                        key={id}
                        value={pickerLabelsIds.includes(name)}
                        onValueChange={noop}
                        isDisabled={isDisabled}
                    />
                ))}
            </FlexCell>
        ) : (
            <PickerList<Label, string>
                dataSource={dataSource}
                value={pickerLabelsIds}
                entityName="location"
                selectionMode="multi"
                // We can't change "id" -> "entity" here
                // as UUI creates new empty row if sorting and valueType="entity" are presented
                valueType="id"
                maxDefaultItems={100}
                maxTotalItems={100}
                sorting={{ field: 'name', direction: 'asc' }}
                onValueChange={(value) => {
                    onValueChange(labels.filter((item) => value?.includes(item.id)));
                }}
            />
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
    onLabelsSelected: (labels: Label[]) => void;
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
                    categories={labels}
                    isLoading={isLoading}
                    hasNextPage={hasNextPage}
                    onFetchNext={onFetchNext}
                    onValueChange={onLabelsSelected}
                    selectedLabels={selectedLabels}
                />
            ) : (
                <Spinner color="sky" />
            )}
        </div>
    );
};
