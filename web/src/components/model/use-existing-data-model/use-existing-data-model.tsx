// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useState } from 'react';
import { mapUndefString } from '../../../shared/helpers/utils';
import { ModelValues } from '../model.models';

import { ILens } from '@epam/uui';
import { FlexRow, LabeledInput, TextInput } from '@epam/loveship';
import styles from './use-existing-data-model.module.scss';

export type AddModelSettingsProps = {
    lens: ILens<ModelValues>;
};

export const UseExistingDataModel: FC<AddModelSettingsProps> = ({ lens }) => {
    const [epochCount, setEpochCount] = useState<string>('');
    return (
        <div className={`${styles.container}`}>
            <div className={styles.content}>
                <h2>Existing training</h2>
                <FlexRow padding="6">
                    <LabeledInput label="Epoch count">
                        <TextInput
                            value={epochCount}
                            onValueChange={mapUndefString(setEpochCount)}
                            placeholder="Epoch count"
                        />
                    </LabeledInput>
                    <LabeledInput label="Score" {...lens.prop('score').toProps()}>
                        <TextInput
                            {...lens.prop('score').toProps()}
                            cx="c-m-t-5"
                            placeholder="Score"
                        />
                    </LabeledInput>
                </FlexRow>
                <FlexRow padding="6" vPadding="24">
                    <LabeledInput label="Data path" />
                </FlexRow>
                <FlexRow padding="6">
                    <LabeledInput label="File" {...lens.prop('data_path_file').toProps()}>
                        <TextInput
                            {...lens.prop('data_path_file').toProps()}
                            cx="c-m-t-5"
                            placeholder="File"
                        />
                    </LabeledInput>
                    <LabeledInput label="Bucket" {...lens.prop('data_path_bucket').toProps()}>
                        <TextInput
                            {...lens.prop('data_path_bucket').toProps()}
                            cx="c-m-t-5"
                            placeholder="Bucket"
                        />
                    </LabeledInput>
                </FlexRow>
            </div>
        </div>
    );
};

export default UseExistingDataModel;
