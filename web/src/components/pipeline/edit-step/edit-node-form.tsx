import { StepFormConnector } from 'connectors/step-form-connector/step-form-connector';
import React, { FC, useMemo } from 'react';
import { StepValues } from './edit-step';
import { Node, XYPosition } from 'react-flow-renderer';
import { PipelineTypes, Step } from 'api/typings';

interface EditNodeFormProps {
    currentElementPosition?: XYPosition;
    availableCategories?: string[];
    step?: Step;
    parentStep?: Step;
    currentNode?: Node;
    node?: Node;
    filterValue?: PipelineTypes;
    parentNode?: Node;
    onSuccess: () => void;
    onSave: (values: StepValues) => void;
}

export const EditNodeForm: FC<EditNodeFormProps> = ({
    parentNode,
    node,
    onSave,
    onSuccess,
    filterValue
}) => {
    const initialValues: StepValues = useMemo<StepValues>(() => {
        return { ...node?.data?.step };
    }, [node?.data?.step]);

    return (
        <StepFormConnector
            availableModels={parentNode?.data?.models}
            filterValue={filterValue}
            onSave={onSave}
            initialValues={initialValues}
            onSuccess={onSuccess}
        />
    );
};
