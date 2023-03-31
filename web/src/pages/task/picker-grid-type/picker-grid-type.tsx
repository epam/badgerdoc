import React, { FC } from 'react';
import { DataPickerRow, FlexRow, PickerInput, Text } from '@epam/loveship';
import { DataRowProps, useArrayDataSource } from '@epam/uui';
import { ValidationType } from 'api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { GridVariants } from 'shared/constants/task';
import horizontalColumns from './horizontalColumns.svg';
import verticalColumns from './verticalColumns.svg';

const OPTIONS = [
    {
        id: GridVariants.horizontal,
        name: 'Horizontal columns',
        icon: horizontalColumns
    },
    {
        id: GridVariants.vertical,
        name: 'Vertical columns',
        icon: verticalColumns
    }
];

type TOption = typeof OPTIONS[0];

export const PickGridType: FC<{ value: GridVariants; onChange: (value: GridVariants) => void }> = ({
    value,
    onChange
}) => {
    const { job, userPages } = useTaskAnnotatorContext();
    const dataSource = useArrayDataSource<TOption, GridVariants, unknown>({ items: OPTIONS }, []);

    if (job?.validation_type !== ValidationType.extensiveCoverage || !userPages.length) return null;

    const renderUserRow = (props: DataRowProps<TOption, GridVariants>) => (
        <DataPickerRow
            {...props}
            key={props.value?.id}
            alignActions="center"
            padding="12"
            renderItem={({ icon, name }) => (
                <FlexRow>
                    <img src={icon} alt={name} />
                    <Text>{name}</Text>
                </FlexRow>
            )}
        />
    );

    return (
        <PickerInput
            valueType="id"
            value={value}
            disableClear
            selectionMode="single"
            dataSource={dataSource}
            renderRow={renderUserRow}
            onValueChange={onChange}
        />
    );
};
