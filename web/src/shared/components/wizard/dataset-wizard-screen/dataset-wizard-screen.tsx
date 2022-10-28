import { datasetsFetcher } from 'api/hooks/datasets';
import { Dataset } from 'api/typings';
import { RadioInput, TextInput } from '@epam/loveship';
import { DatasetPicker } from 'components/dataset-picker/dataset-picker';
import React, { useEffect, useState, FC } from 'react';
import { useEntity } from 'shared/hooks/use-entity';
import styles from './dataset-wizard-screen.module.scss';

export type DatasetWizardScreenResult = {
    datasetName?: string;
    selectedDataset?: Dataset;
    optionId: number;
};

type DatasetWizardScreenProps = {
    onChange: (data: DatasetWizardScreenResult) => void;
};

export const DatasetWizardScreen: FC<DatasetWizardScreenProps> = ({ onChange }) => {
    const [selectedDataset, setDataset] = useState<Dataset>();
    const [datasetName, setDatasetName] = useState<string>();
    const { dataSource } = useEntity<Dataset, Dataset>(datasetsFetcher);
    const [optionId, setOptionId] = useState<number>(1);

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
                <RadioInput value={optionId == 1} onValueChange={() => setOptionId(1)} label="No" />
            </div>
            <div className="form-group">
                <RadioInput
                    value={optionId == 2}
                    onValueChange={() => setOptionId(2)}
                    label="Existing dataset"
                />
                <div className={styles['input-wrapper']}>
                    <DatasetPicker
                        onDatasetSelect={setDataset}
                        dataSource={dataSource}
                        dataset={selectedDataset}
                        disable={optionId !== 2}
                    />
                </div>
            </div>
            <div className="form-group">
                <RadioInput
                    value={optionId == 3}
                    onValueChange={() => setOptionId(3)}
                    label="New dataset"
                />
                <div className={styles['input-wrapper']}>
                    <TextInput
                        value={datasetName}
                        onValueChange={setDatasetName}
                        placeholder="Dataset name"
                        isDisabled={optionId !== 3}
                    />
                </div>
            </div>
        </div>
    );
};
