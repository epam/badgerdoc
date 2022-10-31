import { FlexCell, LabeledInput, PickerInput } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';
import { Pipeline } from 'api/typings';
import React, { FC, useState } from 'react';
import { InfoIcon } from '../../../shared/components/info-icon/info-icon';
import { AutomaticJobProps } from '../automatic-job/automatic-job';
import styles from './pipeline-picker.module.scss';

type PipelineName = {
    id: string;
};

const PipelinePicker: FC<AutomaticJobProps> = ({ lens, pipelines }) => {
    const { value: pipelinePickerValue, onValueChange: setPipelinePickerValue } = {
        ...lens.prop('pipeline').toProps()
    };

    const [pipelineName, setPipelineName] = useState<PipelineName>();

    const correctForm = async (newVal: any) => {
        newVal === null &&
            (await lens.prop('validationType').get()) === 'validation only' &&
            lens.prop('validationType').set(newVal);
        setPipelinePickerValue(newVal);
        return newVal;
    };

    const pipelinesDataSourceUniq = useArrayDataSource<PipelineName, string, any>(
        {
            items: pipelines
                ? pipelines
                      .filter((value, index, self) => {
                          return index === self.findIndex((t) => t.name === value.name);
                      })
                      .map((pipeline) => {
                          return { id: pipeline.name };
                      })
                : []
        },
        [pipelines]
    );

    const usePipelineVersionFilter = () => {
        let pipelinesFiltered =
            pipelines &&
            pipelineName &&
            pipelines.filter((pipeline) => pipeline.name === pipelineName.id);
        return pipelinesFiltered ?? [];
    };
    const pipelineVersionsDataSource = useArrayDataSource<Pipeline, number, any>(
        {
            items: usePipelineVersionFilter()
        },
        [pipelines, pipelineName]
    );

    return (
        <LabeledInput
            cx={`${styles.pipeline} m-t-15`}
            label="ML Pipeline"
            {...lens.prop('pipeline').toProps()}
        >
            <div className="flex align-vert-center">
                <PickerInput
                    value={pipelineName}
                    onValueChange={async (newVal) => {
                        newVal === null && (await correctForm(newVal));
                        setPipelineName(newVal);
                    }}
                    dataSource={pipelinesDataSourceUniq}
                    getName={(item) => item?.id ?? ''}
                    entityName="Pipeline name"
                    selectionMode="single"
                    valueType={'entity'}
                    sorting={{ field: 'id', direction: 'asc' }}
                    placeholder="Select pipeline"
                />
                <FlexCell width={300} cx={'m-l-10'}>
                    <PickerInput
                        value={pipelinePickerValue}
                        onValueChange={(newValue) => correctForm(newValue)}
                        dataSource={pipelineVersionsDataSource}
                        getName={(item) => {
                            if (item.version)
                                return `version-${item.version}${item.is_latest ? '(latest)' : ''}`;
                            return '';
                        }}
                        entityName="Pipeline name"
                        selectionMode="single"
                        valueType={'entity'}
                        sorting={{ field: 'version', direction: 'asc' }}
                        placeholder="Select version"
                    />
                </FlexCell>
                <InfoIcon
                    title="Select pipeline"
                    description="Performs operations on a document for annotation."
                />
            </div>
        </LabeledInput>
    );
};

export default PipelinePicker;
