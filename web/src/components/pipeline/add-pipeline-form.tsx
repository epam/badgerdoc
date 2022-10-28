import React, { FC, useCallback } from 'react';
import { ErrorNotification, SuccessNotification, Text } from '@epam/loveship';
import { Form, INotification } from '@epam/uui';
import { getError } from 'shared/helpers/get-error';
import { useAddPipelineMutation } from 'api/hooks/pipelines';
import { Pipeline, Category, Step, PipelineTypes } from 'api/typings';
import { svc } from 'services';
import { AddPipelineWizardForm } from 'components/pipeline/add-pipeline-wizard-form/add-pipeline-wizard-form';

interface AddPipelineFormProps {
    onPipelineAddSuccess: (id: string) => void;
}

export type PipelineValues = {
    addedPipelineId?: string;
    pipelineName?: string;
    basePipeline?: Pipeline;
    categories?: Category[];
    steps?: Step[];
    isVersion?: boolean;
    type?: 'inference' | 'preprocessing' | string;
    description?: string;
    summary?: string;
};

const initialValues: PipelineValues = {};
const getMetadata = () => ({
    props: {
        pipelineName: { isRequired: true }
    }
});
const AddPipelineForm: FC<AddPipelineFormProps> = ({ onPipelineAddSuccess }) => {
    const renderForm = useCallback((formProps) => <AddPipelineWizardForm {...formProps} />, []);

    const addPipelineMutation = useAddPipelineMutation();

    const handleSave = useCallback(async (values: PipelineValues) => {
        const categories =
            values.categories?.map(({ id }) => String(id)) ??
            values.basePipeline?.meta?.categories ??
            [];
        const pipelineProps: Partial<Pipeline> = {
            meta: {
                original_pipeline_id: values.isVersion
                    ? values.basePipeline?.original_pipeline_id
                    : undefined,
                type: (values.type ?? 'inference') as PipelineTypes,
                name: values.pipelineName,
                categories,
                description: values.description ?? '',
                summary: values.summary ?? ''
            },
            steps: values.steps
        };
        try {
            const response = await addPipelineMutation.mutateAsync(pipelineProps);
            if (response.id) {
                values.addedPipelineId = response.id.toString();
            }
            return {
                form: values
            };
        } catch (err: any) {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(err)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
            return {
                form: values,
                validation: {
                    isInvalid: true
                }
            };
        }
    }, []);

    const handleSuccess = useCallback(
        (values: PipelineValues) => {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <SuccessNotification {...props}>
                        <Text>Pipeline created successfully!</Text>
                    </SuccessNotification>
                ),
                { duration: 2 }
            );
            if (values.addedPipelineId) {
                onPipelineAddSuccess(values.addedPipelineId);
            }
        },
        [onPipelineAddSuccess]
    );

    return (
        <Form<PipelineValues>
            renderForm={renderForm}
            onSave={handleSave}
            value={initialValues}
            getMetadata={getMetadata}
            onSuccess={handleSuccess}
        />
    );
};

export default AddPipelineForm;
