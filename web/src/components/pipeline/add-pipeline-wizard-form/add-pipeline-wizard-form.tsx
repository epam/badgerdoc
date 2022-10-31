import { RenderFormProps } from '@epam/uui';
import { Pipeline, Category, PipelineData, PipelineTypes } from 'api/typings';
import { PipelineValues } from 'components/pipeline/add-pipeline-form';
import React, { FC, useMemo, useEffect, useState } from 'react';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from 'shared/components/wizard/wizard/wizard';
import { PIPELINES_PAGE } from 'shared/constants';
import AddPipelineSettings from '../add-pipeline-settings/add-pipeline-settings';
import { PipelineFormField } from '../pipeline-form-field/pipeline-form-field';
import wizardStyles from '../../../shared/components/wizard/wizard/wizard.module.scss';
import { PipelineTextArea } from '../pipeline-text-area/pipeline-text-area';

type FormProps = RenderFormProps<PipelineValues> & {
    basePipelines?: Pipeline[];
    allCategories?: Category[];
};

export const AddPipelineWizardForm: FC<FormProps> = ({ lens, save }) => {
    const { pipelineName, categories: selectedCategories, basePipeline } = lens.get();

    const pipeline: PipelineData = useMemo(() => {
        const categories = basePipeline
            ? basePipeline?.meta?.categories
            : selectedCategories?.map(({ id }) => String(id));
        const type = lens.get().type as PipelineTypes;

        return {
            name: pipelineName ?? basePipeline?.meta?.name ?? '',
            meta: {
                categories: categories ?? [],
                type: type
            }
        };
    }, [pipelineName, selectedCategories, basePipeline]);

    useEffect(() => {
        lens.prop('steps').set(basePipeline?.steps ?? []);
    }, [basePipeline]);

    const [stepIndex, setStepIndex] = useState(0);
    const handleNext = () => {
        setStepIndex(stepIndex + 1);
    };
    const handlePrev = () => {
        setStepIndex(stepIndex - 1);
    };
    const finishButtonCaption = 'Add Pipeline';

    const steps: WizardPropsStep[] = [
        {
            title: 'Settings',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <AddPipelineSettings lens={lens} />
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
            title: 'Steps',
            content: (
                <div className={wizardStyles['content__wrapper']}>
                    <div className={wizardStyles['content__body']}>
                        <PipelineFormField pipeline={pipeline} {...lens.prop('steps').toProps()} />
                    </div>
                    <div className={wizardStyles['content__editor']}>
                        <PipelineTextArea
                            text={lens.prop('summary').toProps().value}
                            onTextChange={lens.prop('summary').toProps().onValueChange}
                            title={'Short description for a whole pipeline'}
                        />
                        <PipelineTextArea
                            text={lens.prop('description').toProps().value}
                            onTextChange={lens.prop('description').toProps().onValueChange}
                            title={'Full description for a specific version'}
                        />
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
                </div>
            )
        }
    ];
    return <Wizard steps={steps} returnUrl={PIPELINES_PAGE} stepIndex={stepIndex} />;
};
