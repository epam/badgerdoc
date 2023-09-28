// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { Panel, PickerInput } from '@epam/loveship';
import { LazyDataSource } from '@epam/uui';
import { Dataset } from 'api/typings';

import styles from './dataset-picker.module.scss';

type DatasetPickerProps = {
    onDatasetSelect(dataset: Dataset): void;
    dataSource: LazyDataSource<Dataset, Dataset>;
    title?: any | undefined;
    dataset?: Dataset;
    disable?: boolean;
};

export const DatasetPicker: FC<DatasetPickerProps> = ({
    onDatasetSelect,
    dataSource,
    title,
    dataset,
    disable
}) => {
    return (
        <Panel cx={styles['dataset-picker']}>
            {title ? title : null}
            <PickerInput<Dataset | undefined, Dataset>
                dataSource={dataSource}
                value={dataset}
                onValueChange={onDatasetSelect}
                entityName="dataset"
                selectionMode="single"
                valueType="entity"
                isDisabled={disable}
                searchPosition="body"
            />
        </Panel>
    );
};
