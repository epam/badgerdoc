import { LabeledInput, PickerInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { Category, Taxonomy } from 'api/typings';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import React, { FC, Fragment } from 'react';
import { InfoIcon } from '../info-icon/info-icon';

type TaxonomiesPickersProps = {
    categories: Category[] | undefined;
    taxonomies: Taxonomy[] | undefined;
    lens: ILens<JobValues>;
};

type TaxonomyPickerItem = {
    taxonomy: Taxonomy;
    id: string;
    name: string;
};

const makeItem = (taxonomy: Taxonomy): TaxonomyPickerItem => ({
    id: `${taxonomy?.id}${taxonomy?.version}`,
    name: `${taxonomy?.name} - v.${taxonomy?.version}`,
    taxonomy
});

const TaxonomyPickers: FC<TaxonomiesPickersProps> = ({ categories, taxonomies, lens }) => {
    if (!categories?.length) return <></>;

    const items = taxonomies?.map(makeItem);
    const taxonomiesDataSource = useArrayDataSource(
        {
            items: items ?? []
        },
        [taxonomies]
    );

    const extractValue = (categoryId: string): TaxonomyPickerItem | undefined => {
        const taxonomies = lens.prop('selected_taxonomies').get();

        if (taxonomies?.[categoryId]) {
            return makeItem(taxonomies[categoryId]);
        }
    };

    const onValueChange = (categoryId: string, item?: TaxonomyPickerItem) => {
        if (!item) {
            return;
        }
        const { taxonomy } = item;

        const previousValue = lens.prop('selected_taxonomies').get();
        const newValue = previousValue
            ? { ...previousValue, [categoryId]: taxonomy }
            : { [categoryId]: taxonomy };

        lens.prop('selected_taxonomies').set(newValue);
    };

    return (
        <>
            {categories.map((category) => (
                <Fragment key={category.id}>
                    <LabeledInput
                        cx={`m-t-15`}
                        label={category.name}
                        {...lens.prop('selected_taxonomies').toProps()}
                    >
                        <div className="flex align-vert-center">
                            <PickerInput
                                {...lens.prop('selected_taxonomies').toProps()}
                                onValueChange={(newValue) => onValueChange(category.id, newValue)}
                                value={extractValue(category.id)}
                                dataSource={taxonomiesDataSource}
                                entityName={`Taxonomy name`}
                                selectionMode="single"
                                valueType={'entity'}
                                sorting={{ field: 'name', direction: 'asc' }}
                                placeholder="Select taxonomy"
                            />
                            <InfoIcon
                                title="Select Taxonomy"
                                description="Taxonomies which can be used by user."
                            />
                        </div>
                    </LabeledInput>
                </Fragment>
            ))}
        </>
    );
};

export default TaxonomyPickers;
