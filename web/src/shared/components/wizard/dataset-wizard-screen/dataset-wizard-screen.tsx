import { datasetsFetcher } from 'api/hooks/datasets';
import { Dataset } from 'api/typings';
import { RadioInput, TextInput } from '@epam/loveship';
import { DatasetPicker } from 'components/dataset-picker/dataset-picker';
import React, { useEffect, useState, FC } from 'react';
import { useEntity } from 'shared/hooks/use-entity';
import styles from './dataset-wizard-screen.module.scss';
import { DataSetOptions } from './constants';

export type DatasetWizardScreenResult = {
    datasetName?: string;
    selectedDataset?: Dataset;
    optionId: DataSetOptions;
};

type DatasetWizardScreenProps = {
    onChange: (data: DatasetWizardScreenResult) => void;
};

export const DatasetWizardScreen: FC<DatasetWizardScreenProps> = ({ onChange }) => {
    const [selectedDataset, setDataset] = useState<Dataset>();
    const [datasetName, setDatasetName] = useState<string>();
    const [optionId, setOptionId] = useState<DataSetOptions>(DataSetOptions.noDataSet);
    const { dataSource } = useEntity<Dataset, Dataset>(datasetsFetcher);

    useEffect(() => {
        onChange({ optionId, selectedDataset, datasetName });
    }, [optionId, selectedDataset, datasetName]);

    return (
        <div className={`form-wrapper`}>
            <div className={styles['title']}>Do you want to add files to dataset now?</div>
            <div className={styles['description']}>
                Datasets help to organize files, basically they work as file folders.
                <br />
                You might add files to dataset later.
            </div>
            <div className="form-group">
                <RadioInput
                    value={optionId == DataSetOptions.noDataSet}
                    onValueChange={() => setOptionId(DataSetOptions.noDataSet)}
                    label="No"
                />
            </div>
            <div className="form-group">
                <RadioInput
                    value={optionId === DataSetOptions.existingDataSet}
                    onValueChange={() => setOptionId(DataSetOptions.existingDataSet)}
                    label="Existing dataset"
                />
                <div className={styles['input-wrapper']}>
                    <DatasetPicker
                        onDatasetSelect={setDataset}
                        dataSource={dataSource}
                        dataset={selectedDataset}
                        disable={optionId !== DataSetOptions.existingDataSet}
                    />
                </div>
            </div>
            <div className="form-group">
                <RadioInput
                    value={optionId === DataSetOptions.newDataSet}
                    onValueChange={() => setOptionId(DataSetOptions.newDataSet)}
                    label="New dataset"
                />
                <div className={styles['input-wrapper']}>
                    <TextInput
                        value={datasetName}
                        onValueChange={setDatasetName}
                        placeholder="Dataset name"
                        isDisabled={optionId !== DataSetOptions.newDataSet}
                    />
                </div>
            </div>
        </div>
    );
};
