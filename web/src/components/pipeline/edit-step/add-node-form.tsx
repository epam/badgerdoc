// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import { StepFormConnector } from 'connectors/step-form-connector/step-form-connector';
import React, { FC } from 'react';
import { StepValues } from './edit-step';
import { Node } from 'react-flow-renderer';
import { PipelineTypes } from 'api/typings';

const initialValues: StepValues = {};

interface AddNodeFormProps {
    parentNode?: Node;
    onSuccess: () => void;
    onSave: (values: StepValues) => void;
    filterValue?: PipelineTypes;
}

export const AddNodeForm: FC<AddNodeFormProps> = ({
    parentNode,
    onSave,
    onSuccess,
    filterValue
}) => {
    return (
        <StepFormConnector
            filterValue={filterValue}
            availableModels={parentNode?.data?.models}
            onSave={onSave}
            initialValues={initialValues}
            onSuccess={onSuccess}
            saveText="Add"
        />
    );
};
