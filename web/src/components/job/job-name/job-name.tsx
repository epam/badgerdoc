// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import { ILens } from '@epam/uui';
import { LabeledInput, TextInput } from '@epam/loveship';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import React, { FC } from 'react';
import styles from './job-name.module.scss';
import { InfoIcon } from '../../../shared/components/info-icon/info-icon';

type JobNameProps = {
    lens: ILens<JobValues>;
};
const JobName: FC<JobNameProps> = ({ lens }) => {
    return (
        <LabeledInput
            label="Job Name"
            {...lens.prop('jobName').toProps()}
            cx={`m-t-5 ${styles['job-name']}`}
        >
            <div className="flex align-vert-center">
                <TextInput {...lens.prop('jobName').toProps()} placeholder="Job name" />
                <InfoIcon title="" description="" />
            </div>
        </LabeledInput>
    );
};

export default JobName;
