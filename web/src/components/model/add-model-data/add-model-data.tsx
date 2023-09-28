// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useState } from 'react';
import TrainModel from '../train-model/train-model';
import UseExistingDataModel from '../use-existing-data-model/use-existing-data-model';
import { ModelValues } from '../model.models';

import { ILens } from '@epam/uui';
import { MultiSwitch } from '@epam/loveship';
import styles from './add-model-data.module.scss';

export type AddModelDataProps = {
    lens: ILens<ModelValues>;
};
type AddModelStep = 'TrainModel' | 'UseExistingData';
const AddModelData: FC<AddModelDataProps> = ({ lens }) => {
    let currentDataType: AddModelStep = 'TrainModel';
    const [value, onValueChange] = useState<AddModelStep>(currentDataType);
    const model =
        value === 'TrainModel' ? <TrainModel lens={lens} /> : <UseExistingDataModel lens={lens} />;
    return (
        <div className={`${styles.container} flex flex-col form-wrapper`}>
            <div className={styles.header}>
                <MultiSwitch
                    size="42"
                    items={[
                        {
                            id: 'TrainModel',
                            caption: 'TRAIN MODEL'
                        },
                        { id: 'UseExistingData', caption: 'USE EXISTING DATA' }
                    ]}
                    value={value}
                    onValueChange={(item: AddModelStep) => onValueChange(item)}
                />
            </div>
            <div className={styles.content}>{model}</div>
        </div>
    );
};

export default AddModelData;
