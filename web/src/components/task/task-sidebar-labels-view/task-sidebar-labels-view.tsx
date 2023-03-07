import React, { FC, useMemo } from 'react';
import { noop } from 'lodash';

import { PickerList, Spinner, FlexCell, Checkbox } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';

import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { Label, Category } from 'api/typings';

import styles from './task-sidebar-labels-view.module.scss';

type TaskSidebarLabelsViewProps = {
    viewMode: boolean;
    labels?: Category[];
    pickerValue: string[];
    onValueChange: (e: any, labelsArr: Label[]) => void;
    selectedLabels: Label[];
};

export const TaskSidebarLabelsView: FC<TaskSidebarLabelsViewProps> = ({
    viewMode = false,
    labels,
    pickerValue,
    onValueChange,
    selectedLabels
}) => {
    const { task } = useTaskAnnotatorContext();
    const isDisabled = !(task?.status === 'In Progress' || task?.status === 'Ready');
    if (!labels) {
        return <Spinner color="sky" />;
    }

    const labelsArr = useMemo(
        () =>
            labels.map((el: { name: string; id: string }) => {
                return { name: el.name, id: el.id };
            }),
        [labels]
    );

    const dataSource = useArrayDataSource<Label, unknown, unknown>(
        { items: [...selectedLabels, ...labelsArr] },
        [labels]
    );

    const renderData =
        viewMode || isDisabled ? (
            <FlexCell width="auto">
                {labelsArr.map((el) => (
                    <Checkbox
                        cx={styles.checkbox}
                        label={el.name}
                        key={el.id}
                        value={pickerValue.includes(el.name)}
                        onValueChange={noop}
                        isDisabled={isDisabled}
                    />
                ))}
            </FlexCell>
        ) : (
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
        );

    return (
        <div className={`${styles.picker_list} ${viewMode && styles.disabled}`}>{renderData}</div>
    );
};
