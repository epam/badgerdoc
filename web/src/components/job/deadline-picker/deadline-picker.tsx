// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import { DatePicker, LabeledInput } from '@epam/loveship';
import { ILens } from '@epam/uui';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import React, { FC } from 'react';
import styles from './deadline-picker.module.scss';

type DeadlinePickerProps = {
    lens: ILens<JobValues>;
};

const DeadlinePicker: FC<DeadlinePickerProps> = ({ lens }) => {
    const currentDate = new Date().getTime();
    return (
        <LabeledInput
            cx={`${styles['width-small']} p-l-15 m-t-15`}
            label="Deadline"
            {...lens.prop('deadline').toProps()}
        >
            <DatePicker
                {...lens.prop('deadline').toProps()}
                format="DD/MM/YYYY"
                filter={(day) => day.valueOf() >= currentDate}
            />
        </LabeledInput>
    );
};

export default DeadlinePicker;
