import { LabeledInput, PickerInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { Category, Taxonomy } from 'api/typings';
import { JobValues } from 'connectors/add-job-connector/add-job-connector';
import React, { FC, Fragment, useCallback } from 'react';
import { InfoIcon } from '../info-icon/info-icon';

type TaxonomiesPickersProps = {
    categories: Category[] | undefined;
    taxonomies: Taxonomy[] | undefined;
    lens: ILens<JobValues>;
};

const TaxonomyPickers: FC<TaxonomiesPickersProps> = ({ categories, taxonomies, lens }) => {
    if (!categories?.length) return <></>;

    const taxonomiesDataSource = useArrayDataSource(
        {
            items: taxonomies ?? []
        },
        [taxonomies]
    );

    const extractValue = useCallback((categoryId: string): Taxonomy | undefined => {
        const taxonomies = lens.prop('selected_taxonomies').get();

        if (taxonomies) {
            return taxonomies[categoryId];
        }
    }, []);

    const onValueChange = useCallback((categoryId: string, taxonomy?: Taxonomy) => {
        if (!taxonomy) {
            return;
        }

        const previousValue = lens.prop('selected_taxonomies').get();
        const newValue = previousValue
            ? { ...previousValue, [categoryId]: taxonomy }
            : { [categoryId]: taxonomy };

        lens.prop('selected_taxonomies').set(newValue);
    }, []);

    return (
        <>
            {categories.map((category, index) => (
                <Fragment key={index}>
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
                                getName={(item) => item?.name ?? ''}
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
