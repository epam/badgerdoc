import React, { FC } from 'react';
import { LabeledInput, NumericInput } from '@epam/loveship';
import { ILens } from '@epam/uui';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import styles from './extensive-coverage-input.module.scss';

interface Props {
    lens: ILens<JobValues>;
}

export const ExtensiveCoverageInput: FC<Props> = ({ lens }) => (
    <>
        <LabeledInput
            cx={`m-t-15 ${styles.coverage}`}
            label="Extensive Coverage Number"
            {...lens.prop('extensive_coverage').toProps()}
        >
            <NumericInput max={3} min={1} {...lens.prop('extensive_coverage').toProps()} />
        </LabeledInput>
    </>
);
