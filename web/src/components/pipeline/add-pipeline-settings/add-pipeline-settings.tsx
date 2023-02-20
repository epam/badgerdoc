import React, { FC, useState } from 'react';
import { PipelineValues } from 'components/pipeline/add-pipeline-form';
import { pipelinesFetcher } from 'api/hooks/pipelines';
import { useEntity } from 'shared/hooks/use-entity';
import { Pipeline } from 'api/typings';

import { LabeledInput, PickerInput, TextInput, Checkbox } from '@epam/loveship';
import { ILens, useArrayDataSource } from '@epam/uui';
import styles from './add-pipeline-settings.module.scss';

export type AddPipelineSettingsProps = {
    lens: ILens<PipelineValues>;
};

type PipelineTypes = {
    id: string;
    type: string;
};

const AddPipelineSettings: FC<AddPipelineSettingsProps> = ({ lens }) => {
    const { dataSource: pipelinesDataSource } = useEntity(pipelinesFetcher);
    const [value, onValueChange] = useState(false);
    const basePipeline = lens.prop('basePipeline').toProps().value;
    const isVersion = lens.prop('isVersion').toProps().value;
    const type = lens.prop('type').toProps().value;
    const setType = lens.prop('type').toProps().onValueChange;
    const pipelineName = lens.prop('pipelineName').toProps().value;
    const typesDatasource = useArrayDataSource(
        {
            items: [
                { id: 'inference', type: 'Extraction' },
                { id: 'preprocessing', type: 'Preprocessing' }
            ] as PipelineTypes[]
        },
        []
    );

    return (
        <div className={`${styles.container} flex flex-col`}>
            <LabeledInput
                cx={`${styles.pipeline} ${styles['m-b-1']}`}
                label="Base on existing pipeline"
            >
                <PickerInput
                    value={basePipeline}
                    onValueChange={(newValue: any) => {
                        lens.set({
                            ...lens.get(),
                            basePipeline: newValue as Pipeline,
                            pipelineName: newValue?.name,
                            isVersion: !!newValue,
                            type: newValue?.meta?.type
                        } as PipelineValues);
                        onValueChange(!value);
                    }}
                    dataSource={pipelinesDataSource}
                    getName={(item) => item?.name ?? ''}
                    entityName="Pipeline name"
                    selectionMode="single"
                    valueType={'entity'}
                    sorting={{ field: 'name', direction: 'asc' }}
                    placeholder="Select a pipeline"
                />
            </LabeledInput>
            <LabeledInput cx={`${styles.pipeline} ${styles['m-b-1']}`} label="Choose type">
                <PickerInput
                    value={type}
                    onValueChange={setType}
                    dataSource={typesDatasource}
                    getName={(item) => item?.type ?? ''}
                    entityName="type"
                    selectionMode="single"
                    valueType={'id'}
                    placeholder="Select a type"
                />
            </LabeledInput>
            <Checkbox
                {...lens.prop('isVersion').toProps()}
                label="Create a new version of existing pipeline?"
                isDisabled={!basePipeline}
                cx={styles['m-b-1']}
            />
            <LabeledInput label="Pipeline Name" {...lens.prop('pipelineName').toProps()}>
                <TextInput
                    value={pipelineName}
                    onValueChange={(newValue) => {
                        const lensValues = lens.get();
                        lens.set({
                            ...lensValues,
                            pipelineName: newValue as string,
                            type: lensValues.type ?? 'inference'
                        } as PipelineValues);
                        onValueChange(!value);
                    }}
                    cx={`${styles['pipeline-name']} m-t-5`}
                    placeholder={'Pipeline name'}
                    isDisabled={isVersion && !!basePipeline}
                />
            </LabeledInput>
        </div>
    );
};

export default AddPipelineSettings;
