import React, { FC, useState } from 'react';
import styles from './train-model-setting.module.scss';
import { FlexRow, LabeledInput, PickerInput, TextInput } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import { mapUndefString } from '../../../shared/helpers/utils';
import { ModelValues } from 'connectors/add-model-connector/add-model-connector';

export type AddModelSettingsProps = {
    lens: ILens<ModelValues>;
};

export const TrainModelSetting: FC<AddModelSettingsProps> = ({ lens }) => {
    const modelToBaseDataSource = useArrayDataSource(
        {
            items: [
                {
                    id: 'Google Colab',
                    value: 1
                },
                {
                    id: 'Local',
                    value: 2
                }
            ]
        },
        []
    );
    const [modelToBase, setModelToBase] = useState<number>();
    const handlePickerChange = (value: number) => {
        const trainingId = modelToBaseDataSource.getById(value).value;
        lens.prop('training_id').set(trainingId);
        setModelToBase(value);
    };
    const [valueID, setValueID] = useState<string>('');
    const [modelName, setModelName] = useState<string>('');
    return (
        <div className={`${styles.container}`}>
            <div className={styles.content}>
                <h2>Settings for new training</h2>
                <FlexRow padding="6" vPadding="24">
                    <LabeledInput
                        cx={`m-t-15`}
                        label="Training mode"
                        {...lens.prop('training_id').toProps()}
                    >
                        <PickerInput
                            {...lens.prop('training_id').toProps()}
                            entityName="Training mode"
                            placeholder="Seletct training"
                            onValueChange={handlePickerChange}
                            //@ts-ignore
                            getName={(item) => item?.id ?? 0}
                            valueType="id"
                            selectionMode="single"
                            value={modelToBase}
                            minBodyWidth={100}
                            disableClear={true}
                            dataSource={modelToBaseDataSource}
                        />
                    </LabeledInput>
                </FlexRow>
                <FlexRow padding="6" vPadding="24">
                    <LabeledInput label="Epoch count">
                        <TextInput value={valueID} onValueChange={mapUndefString(setValueID)} />
                    </LabeledInput>
                </FlexRow>
                <FlexRow padding="6" vPadding="24">
                    <LabeledInput label="Kubeflow Pipeline ID">
                        <TextInput value={modelName} onValueChange={mapUndefString(setModelName)} />
                    </LabeledInput>
                </FlexRow>
            </div>
        </div>
    );
};

export default TrainModelSetting;
