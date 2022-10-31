import { LabeledInput, PickerInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { Basement } from 'api/typings';
import { ModelValues } from 'connectors/add-model-connector/add-model-connector';
import React, { FC } from 'react';

type BasementPickerProps = {
    lens: ILens<ModelValues>;
    basements: Basement[] | undefined;
};

const BasementPicker: FC<BasementPickerProps> = ({ lens, basements }) => {
    const basementsDataSource = useArrayDataSource(
        {
            items: basements ?? []
        },
        [basements]
    );
    return (
        <LabeledInput
            cx={`m-t-15`}
            label="Basement"
            {...lens.prop('basement').toProps()}
            isRequired
        >
            <PickerInput
                {...lens.prop('basement').toProps()}
                dataSource={basementsDataSource}
                getName={(item) => item?.id ?? ''}
                entityName="Basement name"
                selectionMode="single"
                valueType={'entity'}
                sorting={{ field: 'id', direction: 'asc' }}
                placeholder="Select basement"
            />
        </LabeledInput>
    );
};

export default BasementPicker;
