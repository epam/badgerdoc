import React, { FC } from 'react';

import { Basement } from 'api/typings';
import { ModelValues } from '../model.models';

import { ILens, useArrayDataSource } from '@epam/uui';
import { LabeledInput, PickerInput } from '@epam/loveship';

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
