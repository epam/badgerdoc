import { PipelineData, Step } from 'api/typings';
import { createFlowElements } from 'components/pipeline/pipeline-utils/create-flow-elements';
import React, { useState, useEffect, useMemo, FC } from 'react';
import ReactFlow, { FlowElement } from 'react-flow-renderer';
import EditStep from '../edit-step/edit-step';
import styles from './pipeline-component.module.scss';
import { getLayoutedElements } from '../pipeline-utils/get-layouted-elements';
import { usePipelineEditor } from './use-pipeline-editor';
import { useArrayDataSource } from '@epam/uui';
import { PickerInput } from '@epam/loveship';

type PipelineComponentProps = {
    pipeline?: PipelineData | null;
    readOnly?: boolean;
    onAddStep?: (newStep: Step, parentStepId?: string) => void;
    onUpdateStep?: (step: Step) => void;
    onDeleteStep?: (step: Step) => void;
    currentVersion?: number;
    latestVersion?: number;
    changeVersion?: (value: number) => void;
};

export const PipelineComponent: FC<PipelineComponentProps> = ({
    pipeline,
    readOnly,
    onAddStep,
    onUpdateStep,
    onDeleteStep,
    currentVersion,
    latestVersion,
    changeVersion
}) => {
    const [flowElements, setFlowElements] = useState<FlowElement | any>([]);

    const { flowProps, editStepProps, showAdd } = usePipelineEditor(
        flowElements,
        onAddStep,
        onUpdateStep,
        onDeleteStep
    );
    const nodes: FlowElement[] = useMemo(() => {
        return pipeline ? createFlowElements({ ...pipeline, steps: pipeline.steps ?? [] }) : [];
    }, [pipeline]);

    useEffect(() => {
        setFlowElements(getLayoutedElements(nodes));
    }, [nodes]);

    let versionsArray = [];
    if (latestVersion) {
        let i = 1;
        while (i < latestVersion) {
            const item = {
                id: i,
                text: `version ${i}.0`
            };
            versionsArray.push(item);
            i++;
        }
        versionsArray.push({ id: i, text: `version ${i}.0 - latest` });
    }
    const versionsDS = useArrayDataSource(
        {
            items: versionsArray
        },
        []
    );

    return (
        <div className={styles['pipeline-container']}>
            {!!latestVersion && (
                <div style={{ width: 'fit-content' }}>
                    <PickerInput
                        dataSource={versionsDS}
                        selectionMode="single"
                        value={currentVersion}
                        valueType="id"
                        entityName="Pipeline version"
                        getName={(item) => item?.text || ''}
                        onValueChange={(value) => {
                            if (changeVersion && typeof value === 'number') changeVersion(value);
                        }}
                        size="36"
                        disableClear={true}
                    />
                </div>
            )}
            <ReactFlow {...flowProps} elements={flowElements} style={{ overflow: 'unset' }} />
            {!readOnly && showAdd && (
                <EditStep {...{ ...editStepProps, filterValue: pipeline?.meta?.type }} />
            )}
        </div>
    );
};

export default PipelineComponent;
