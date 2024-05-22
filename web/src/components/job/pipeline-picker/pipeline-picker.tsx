// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useEffect, useState, useMemo } from 'react';
import { Pipeline, PipelineManager, SortingDirection } from 'api/typings';
import { InfoIcon } from '../../../shared/components/info-icon/info-icon';
import { AutomaticJobProps } from '../automatic-job/automatic-job';

import { FlexCell, LabeledInput, PickerInput, RadioGroup } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';
import styles from './pipeline-picker.module.scss';
import { usePipelines } from '../../../api/hooks/pipelines';

type PipelineName = {
    id: string;
};

const PipelinePicker: FC<AutomaticJobProps> = ({ lens, pipelineManagers = [] }) => {
    const { value: pipelinePickerValue, onValueChange: setPipelinePickerValue } = {
        ...lens.prop('pipeline').toProps()
    };

    const items = useMemo(() => {
        return pipelineManagers.map((manager) => ({ name: manager.name, id: manager.name }));
    }, [pipelineManagers]);

    const [pipelineName, setPipelineName] = useState<PipelineName>();
    const [pipelines, setPipelines] = useState<Pipeline[] | undefined>();

    const [currentPipelineManager, setCurrentPipelineManager] = useState<
        PipelineManager | undefined
    >();

    useEffect(() => {
        if (pipelineManagers && pipelineManagers.length > 0) {
            setCurrentPipelineManager(pipelineManagers[0]);
        }
    }, [pipelineManagers]);

    const { data: pipelinesResponse, isLoading } = usePipelines({
        resource: currentPipelineManager?.resource
    });

    useEffect(() => {
        if (pipelinesResponse?.data) {
            setPipelines(pipelinesResponse.data);
        }
    }, [pipelinesResponse]);

    const correctForm = async (newVal: any) => {
        if (newVal === null) {
            (await lens.prop('validationType').get()) === 'validation only' &&
                lens.prop('validationType').set(newVal);
        } else {
            const chosenPipeline = pipelines?.find((pipeline) => pipeline.name === newVal.id);
            if (chosenPipeline) {
                setPipelinePickerValue(chosenPipeline);
            }
        }
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

    const onChangePipeLineManager = (value: string) => {
        const newManager = pipelineManagers?.find((manager) => manager.name === value);
        setCurrentPipelineManager(newManager);
    };

    return (
        <>
            <LabeledInput cx={`${styles.pipeline} m-t-15`} label="Choose a pipeline manager">
                <div className="flex align-vert-center">
                    <RadioGroup
                        items={items}
                        value={currentPipelineManager?.name}
                        onValueChange={onChangePipeLineManager}
                        direction="horizontal"
                        cx="selection-mode-toggle"
                    />
                </div>
            </LabeledInput>
            <LabeledInput
                cx={`${styles.pipeline} m-t-15`}
                label="ML Pipeline"
                {...lens.prop('pipeline').toProps()}
            >
                <div className="flex align-vert-center">
                    <PickerInput
                        value={pipelineName}
                        onValueChange={async (newVal) => {
                            await correctForm(newVal);
                            setPipelineName(newVal);
                        }}
                        dataSource={pipelinesDataSourceUniq}
                        getName={(item) => item?.id ?? ''}
                        entityName="Pipeline name"
                        selectionMode="single"
                        valueType={'entity'}
                        sorting={{ field: 'id', direction: 'asc' }}
                        placeholder="Select pipeline"
                        isDisabled={isLoading}
                    />
                    <InfoIcon
                        title="Select pipeline"
                        description="Performs operations on a document for annotation."
                    />
                </div>
            </LabeledInput>
        </>
    );
};

export default PipelinePicker;
