import React, { FC, useCallback, useState } from 'react';
import AddModelSettings from 'components/model/add-model-settings/add-model-settings';
import AddModelData from 'components/model/add-model-data/add-model-data';
import { useAddModelMutation, useEditModelMutation, useModels } from 'api/hooks/models';
import { useCategories } from 'api/hooks/categories';
import { Model, SortingDirection } from 'api/typings';
import { useBasements } from 'api/hooks/basements';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from 'shared/components/wizard/wizard/wizard';
import { MODELS_PAGE } from 'shared/constants/general';
import { ModelValues, ActionTypeEnum } from '../../components/model/model.models';

import { Form, IFormApi } from '@epam/uui';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type FormModelConnectorProps = {
    onModelSubmit: () => void;
    onError: (err: any) => void;
    actionType: ActionTypeEnum;
};

const initialValues: ModelValues = {
    id: ''
};

const FormModelConnector: FC<FormModelConnectorProps> = ({
    onModelSubmit,
    onError,
    actionType
}) => {
    const [stepIndex, setStepIndex] = useState<number>(0);
    const handleNext = () => {
        setStepIndex((prev) => prev + 1);
    };
    const handlePrev = () => {
        setStepIndex((prev) => prev - 1);
    };
    const finishButtonCaption = actionType === ActionTypeEnum.ADD ? 'Add Model' : 'Edit Model';

    const { data: categories } = useCategories(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const { data: models } = useModels(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC },
            filters: []
        },
        {}
    );

    const { data: basements } = useBasements(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const renderForm = useCallback(
        ({ lens, save }: IFormApi<ModelValues>) => {
            const steps: WizardPropsStep[] = [
                {
                    title: 'Model',
                    content: (
                        <>
                            <div className={wizardStyles['content__body']}>
                                <AddModelSettings
                                    lens={lens}
                                    categories={categories?.data}
                                    basements={basements?.data}
                                    models={models?.data}
                                />
                            </div>
                            <div className={wizardStyles['content__footer']}>
                                {renderWizardButtons({
                                    onNextClick: handleNext
                                })}
                            </div>
                        </>
                    )
                },
                {
                    title: 'Data',
                    content: (
                        <>
                            <div className={wizardStyles['content__body']}>
                                <AddModelData lens={lens} />
                            </div>
                            <div className={wizardStyles['content__footer']}>
                                {renderWizardButtons({
                                    onPreviousClick: handlePrev,
                                    onNextClick: () => {
                                        save();
                                    },
                                    nextButtonCaption: finishButtonCaption
                                })}
                            </div>
                        </>
                    )
                }
            ];
            return <Wizard steps={steps} returnUrl={MODELS_PAGE} stepIndex={stepIndex} />;
        },
        [stepIndex, basements]
    );

    const getModelMutationHook = (actionType: ActionTypeEnum) => {
        switch (actionType) {
            case ActionTypeEnum.ADD:
                return useAddModelMutation();
            case ActionTypeEnum.EDIT:
                return useEditModelMutation();
            default:
                return useAddModelMutation();
        }
    };

    const modelMutation = getModelMutationHook(actionType);

    const handleSave = useCallback(async (values: ModelValues) => {
        let categories: (string | number)[] = [];
        if (values.jobs) {
            values.jobs.forEach((el) => {
                categories.push(...el.categories);
            });
        } else {
            values.categories?.forEach((el) => {
                categories.push(el.name);
            });
        }
        const model: Model = {
            id: values.id,
            name: values.name || '',
            basement: values.basement?.id || '',
            categories: categories.map((el) => el.toString()),
            type: values.type,
            training_id: values.training_id,
            score: parseInt(values.score || ''),
            data_path: {
                file: values.data_path_file || '',
                bucket: values.data_path_bucket || ''
            },
            configuration_path: {
                file: values.configuration_path_file || '',
                bucket: values.configuration_path_bucket || ''
            }
        };
        try {
            const response = await modelMutation.mutateAsync(model);
            values.id = response.id;
        } catch (err: any) {
            onError(err);
            return {
                form: values,
                validation: {
                    isInvalid: true
                }
            };
        }
    }, []);

    return (
        <Form
            renderForm={renderForm}
            onSave={handleSave}
            value={initialValues}
            onSuccess={onModelSubmit}
        />
    );
};

export default FormModelConnector;
