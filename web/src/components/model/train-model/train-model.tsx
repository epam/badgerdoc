import React, { FC } from 'react';
import TrainModelSetting from '../train-model-setting/train-model-setting';
import TrainModelJob from '../train-model-job/train-model-job';
import { ModelValues } from '../model.models';

import { ILens } from '@epam/uui';
import styles from './train-model.module.scss';

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
