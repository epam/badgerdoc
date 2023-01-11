import React, { FC, useCallback, useState } from 'react';
import AddModelSettings from 'components/model/add-model-settings/add-model-settings';
import AddModelData from 'components/model/add-model-data/add-model-data';
import { Form, IFormApi } from '@epam/uui';
import { useAddModelMutation, useModels } from 'api/hooks/models';
import { useCategories } from 'api/hooks/categories';
import { Basement, Category, Model, SortingDirection } from 'api/typings';
import { useBasements } from 'api/hooks/basements';
import { Job } from 'api/typings/jobs';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from 'shared/components/wizard/wizard/wizard';
import { MODELS_PAGE } from 'shared/constants';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type AddModelConnectorProps = {
    onModelAdded: () => void;
    onError: (err: any) => void;
};

export type ModelValues = {
    baseModel?: Model;
    name: string | undefined;
    basement: Basement | undefined;
    categories: Category[] | undefined;
    id: string;
    score: string | undefined;
    status?: string;
    type: string | undefined;
    tenant?: string | undefined;
    training_id?: number | undefined;
    configuration_path_file?: string | undefined;
    configuration_path_bucket?: string | undefined;
    data_path_file?: string | undefined;
    data_path_bucket?: string | undefined;
    jobs: Job[] | undefined;
};

const initialValues: ModelValues = {
    name: undefined,
    basement: undefined,
    categories: undefined,
    id: '',
    score: undefined,
    type: undefined,
    training_id: undefined,
    configuration_path_file: undefined,
    configuration_path_bucket: undefined,
    data_path_file: undefined,
    data_path_bucket: undefined,
    jobs: undefined
};

const AddModelConnector: FC<AddModelConnectorProps> = ({ onModelAdded, onError }) => {
    const getMetadata = () => ({
        props: {}
    });

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

    const [stepIndex, setStepIndex] = useState(0);
    const handleNext = () => {
        setStepIndex(stepIndex + 1);
    };
    const handlePrev = () => {
        setStepIndex(stepIndex - 1);
    };
    const finishButtonCaption = 'Add Model';

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
        [stepIndex]
    );

    const handleSave = useCallback(async (values: ModelValues) => {
        let categories: (string | number)[] = [];
        if (values.jobs) {
            values.jobs.forEach((el) => {
                categories = [...categories, ...el.categories];
            });
        } else {
            values.categories?.forEach((el) => {
                categories = [...categories, el.name];
            });
        }
        categories.map((el) => {
            return el.toString();
        });
        const model: Model = {
            id: values.id,
            name: values.name || '',
            basement: values.basement?.id || '',
            categories: categories as string[],
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
            const response = await addModelMutation.mutateAsync(model);
            values.id = response.id;
            return {
                form: values
            };
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

    const addModelMutation = useAddModelMutation();

    return (
        <Form
            renderForm={renderForm}
            onSave={handleSave}
            value={initialValues}
            getMetadata={getMetadata}
            onSuccess={onModelAdded}
        />
    );
};

export default AddModelConnector;
