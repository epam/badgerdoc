import { LabeledInput, PickerInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { Category } from 'api/typings';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import { ModelValues } from 'connectors/add-model-connector/add-model-connector';
import React, { FC } from 'react';
import { InfoIcon } from '../info-icon/info-icon';

type CategoriesPickerProps = {
    lens: ILens<JobValues | ModelValues>;
    categories: Category[] | undefined;
};

const CategoriesPicker: FC<CategoriesPickerProps> = ({ lens, categories }) => {
    const categoriesDataSource = useArrayDataSource(
        {
            items: categories ?? []
        },
        [categories]
    );

    return (
        <LabeledInput cx={`m-t-15`} label="Categories" {...lens.prop('categories').toProps()}>
            <div className="flex align-vert-center">
                <PickerInput
                    {...lens.prop('categories').toProps()}
                    dataSource={categoriesDataSource}
                    getName={(item) => item?.name ?? ''}
                    entityName="Categories name"
                    selectionMode="multi"
                    valueType={'entity'}
                    sorting={{ field: 'name', direction: 'asc' }}
                    placeholder="Select categories"
                />
                <InfoIcon
                    title="Select Categories"
                    description="Categories of text available for annotation to users."
                />
            </div>
        </LabeledInput>
    );
};

export default CategoriesPicker;
