import { Form } from '@epam/uui';
import { useModels, useBasements } from 'api/hooks/models';
import { SortingDirection, Model, Operators, PipelineTypes } from 'api/typings';
import { StepValues } from 'components/pipeline/edit-step/edit-step';
import { StepFormFields } from 'components/pipeline/edit-step/step-form-fields';
import React, { FC, useMemo } from 'react';

interface StepFormConnectorProps {
    availableModels?: string[];
    onSave: (values: StepValues) => void;
    initialValues: StepValues;
    onSuccess: () => void;
    saveText?: string;
    filterValue?: PipelineTypes;
}

export const StepFormConnector: FC<StepFormConnectorProps> = ({
    filterValue,
    availableModels,
    onSave,
    initialValues,
    onSuccess,
    saveText = 'Save'
}) => {
    const getMetadata = () => ({
        props: {
            model: { isRequired: true },
            categories: { isRequired: false },
            args: {
                props: {}
            }
        }
    });

    const { data: models } = useModels(
        {
            page: 1,
            size: 100,
            searchText: '',
            // TODO: filter equals to filterValue
            filters: [
                {
                    field: 'type',
                    operator: filterValue === 'preprocessing' ? Operators.EQ : Operators.IS_NULL,
                    value: filterValue
                }
            ],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const stepCategoriesData = useMemo(() => {
        if (!models || !availableModels) {
            return [];
        }
        const modelsData: Model[] = models.data.filter((model) =>
            availableModels.includes(model.name)
        );
        const categoriesArr = modelsData.flatMap((model) => model.categories ?? []);
        const uniqueCategories = Array.from(new Set(categoriesArr));
        return uniqueCategories.map((name) => ({ id: name, name }));
    }, [models, availableModels]);

    const { data: basements } = useBasements(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC },
            filters: []
        },
        {}
    );

    const handleSave = async (values: StepValues) => {
        onSave(values);
        return {
            form: values
        };
    };

    return (
        <Form<StepValues>
            renderForm={(formProps) => (
                <>
                    <StepFormFields
                        {...formProps}
                        models={models?.data ?? []}
                        stepCategories={stepCategoriesData}
                        basements={basements?.data}
                        saveText={saveText}
                    />
                </>
            )}
            onSave={handleSave}
            value={initialValues}
            getMetadata={getMetadata}
            onSuccess={onSuccess}
        />
    );
};
