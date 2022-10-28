import { LabeledInput, PickerInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { Model } from 'api/typings';
import { ModelValues } from 'connectors/add-model-connector/add-model-connector';
import React, { FC } from 'react';

type ModelPickerProps = {
    lens: ILens<ModelValues>;
    models: Model[] | undefined;
};

const ModelPicker: FC<ModelPickerProps> = ({ lens, models }) => {
    const modelsDataSource = useArrayDataSource(
        {
            items: models ?? []
        },
        [models]
    );
    return (
        <LabeledInput cx={`m-t-15`} label="Base Model" {...lens.prop('baseModel').toProps()}>
            <PickerInput
                {...lens.prop('baseModel').toProps()}
                dataSource={modelsDataSource}
                getName={(item) => item?.name ?? ''}
                entityName="Model name"
                selectionMode="single"
                valueType={'entity'}
                sorting={{ field: 'name', direction: 'asc' }}
                placeholder="Select base model"
            />
        </LabeledInput>
    );
};

export default ModelPicker;
