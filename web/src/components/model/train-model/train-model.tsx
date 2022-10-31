import React, { FC } from 'react';
import styles from './train-model.module.scss';
import TrainModelSetting from '../train-model-setting/train-model-setting';
import TrainModelJob from '../train-model-job/train-model-job';
import { ILens } from '@epam/uui';
import { ModelValues } from 'connectors/add-model-connector/add-model-connector';

export type AddModelSettingsProps = {
    lens: ILens<ModelValues>;
};

export const TrainModel: FC<AddModelSettingsProps> = ({ lens }) => {
    return (
        <div className={`${styles.container} flex`}>
            <TrainModelSetting lens={lens} />
            <TrainModelJob lens={lens} />
        </div>
    );
};

export default TrainModel;
