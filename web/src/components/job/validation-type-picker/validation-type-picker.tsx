import { PickerInput, LabeledInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { ValidationType } from 'api/typings';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import React, { FC } from 'react';
import styles from './validation-type-picker.module.scss';
import { InfoIcon } from '../../../shared/components/info-icon/info-icon';

type ValidationTypePickerProps = {
    lens: ILens<JobValues>;
};

type ValidationTypeChoice = {
    id: ValidationType;
    caption: string;
};

const ValidationTypePicker: FC<ValidationTypePickerProps> = ({ lens }) => {
    const pipeline = lens.prop('pipeline').get();
    const validationTypes: ValidationTypeChoice[] = [
        { id: 'cross', caption: 'Cross validation' },
        { id: 'hierarchical', caption: 'Hierarchical validation' },
        { id: 'validation only', caption: 'Validation only' },
        { id: 'extensive_coverage', caption: 'Extensive Coverage' }
    ];

    const validationTypesData = pipeline
        ? validationTypes
        : validationTypes.filter((type) => type.id !== 'validation only');

    const validationTypeDataSource = useArrayDataSource({ items: validationTypesData }, []);

    return (
        <LabeledInput
            cx={`${styles.width} m-t-15`}
            label="Validation Type"
            {...lens.prop('validationType').toProps()}
        >
            <div className="flex align-vert-center">
                <PickerInput
                    {...lens.prop('validationType').toProps()}
                    value={lens.prop('validationType').get()}
                    dataSource={validationTypeDataSource}
                    getName={(item) => item?.caption ?? ''}
                    entityName="Validation Types"
                    selectionMode="single"
                    valueType="id"
                    sorting={{ field: 'caption', direction: 'asc' }}
                    placeholder="Select validation type"
                />
                <InfoIcon
                    title="Select validation type"
                    description={
                        <ol>
                            <li>
                                <i>Cross validation</i> – each team member validates his peer’s
                                work.
                            </li>
                            <li>
                                <i>Extensive validation coverage</i> - each document page should be
                                annotated by more than one annotator. The difference between
                                annotation of different annotator is{' '}
                                <i>inter annotator agreement</i>. If IAG &gt; 75 then the page is
                                validated. (out of scope for MVP)
                            </li>
                            <li>
                                <i>Hierarchical validation</i> – Validators assigned to check
                                annotation quality and submit annotations for training or re-work.
                            </li>
                        </ol>
                    }
                />
            </div>
        </LabeledInput>
    );
};

export default ValidationTypePicker;
