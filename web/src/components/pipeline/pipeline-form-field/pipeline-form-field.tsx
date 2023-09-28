// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useMemo } from 'react';
import { PipelineData, Step } from 'api/typings';
import { noop } from 'lodash';
import PipelineComponent from '../pipeline-component/pipeline-component';
import { updatePipelineStep } from '../pipeline-utils/update-pipeline-step';

type PipelineFormFieldProps = {
    pipeline?: PipelineData | null;
    value?: Step[];
    onValueChange?: (newValue: Step[]) => void;
};

export const PipelineFormField: FC<PipelineFormFieldProps> = ({
    pipeline,
    value,
    onValueChange = noop
}) => {
    const fullPipeline: PipelineData | null | undefined = useMemo(() => {
        if (!pipeline) {
            return;
        }
        return {
            ...pipeline,
            steps: value ?? []
        };
    }, [pipeline, value]);

    const componentKey = useMemo(() => Math.random(), [fullPipeline]);

    const handleAddStep = (newStep: Step, parentStepId?: string) => {
        const prevValue = value ?? [];
        let newValue: Step[];
        if (parentStepId) {
            newValue = updatePipelineStep(prevValue, parentStepId, (step) => {
                const steps = step.steps ?? [];
                return {
                    ...step,
                    steps: [...steps, newStep]
                };
            });
        } else {
            newValue = [...prevValue, newStep];
        }
        onValueChange(newValue);
    };

    const handleEditStep = (update: Step) => {
        const prevValue = value ?? [];
        let newValue: Step[] = updatePipelineStep(prevValue, update.id, (step) => {
            return {
                ...step,
                ...update
            };
        });
        onValueChange(newValue);
    };
    const handleDeleteStep = (deleteStep: Step, parentStepId?: string) => {
        const prevValue = value ?? [];
        let newValue: Step[];
        if (parentStepId) {
            newValue = updatePipelineStep(prevValue, parentStepId, (parentStep) => {
                const steps = parentStep.steps ?? [];
                return {
                    ...parentStep,
                    steps: steps.filter((step) => step.id !== deleteStep.id)
                };
            });
        } else {
            newValue = prevValue.filter((step) => step.id !== deleteStep.id);
        }
        onValueChange(newValue);
    };
    return (
        <PipelineComponent
            key={componentKey}
            pipeline={fullPipeline}
            onAddStep={handleAddStep}
            onUpdateStep={handleEditStep}
            onDeleteStep={handleDeleteStep}
        />
    );
};
