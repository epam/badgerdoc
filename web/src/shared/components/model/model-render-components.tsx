// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import { FlexRow, LabeledInput, PickerInput, TextInput } from '@epam/loveship';
import { ArrayDataSource } from '@epam/uui';
import { mapUndefString } from '../../../shared/helpers/utils';

export type IItemConfigView<TValue extends string, TData> = {
    labelName: string;
    type: string;
    isRequired: boolean;
    value: {
        value: TValue;
        valueChange(newValue: TValue | string): void;
        dataSource?: ArrayDataSource<TData>;
    };
};

export function renderView<TValue extends string, TData>(
    itemConfigView: IItemConfigView<TValue, TData>
) {
    if (itemConfigView.type === 'pickerInput' && itemConfigView.value.dataSource) {
        return (
            <FlexRow padding="6" vPadding="24">
                <LabeledInput
                    label={itemConfigView.labelName}
                    isRequired={itemConfigView.isRequired}
                >
                    <PickerInput
                        onValueChange={itemConfigView.value.valueChange}
                        //@ts-ignore
                        getName={(item) => item?.name ?? 'test'}
                        valueType="id"
                        selectionMode="single"
                        value={itemConfigView.value.value}
                        minBodyWidth={100}
                        disableClear={true}
                        dataSource={itemConfigView.value.dataSource}
                    />
                </LabeledInput>
            </FlexRow>
        );
    } else if (itemConfigView.type === 'textInput') {
        return (
            <FlexRow padding="6" vPadding="24">
                <LabeledInput
                    label={itemConfigView.labelName}
                    isRequired={itemConfigView.isRequired}
                >
                    <TextInput
                        value={itemConfigView.value.value}
                        onValueChange={mapUndefString(itemConfigView.value.valueChange)}
                    />
                </LabeledInput>
            </FlexRow>
        );
    }
    return null;
}
