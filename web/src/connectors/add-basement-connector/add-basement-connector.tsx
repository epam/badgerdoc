import React, { FC, useCallback, useEffect } from 'react';
import { Form, INotification, RenderFormProps } from '@epam/uui';
import { ErrorNotification, Text } from '@epam/loveship';
import { svc } from 'services';
import { getError } from '../../shared/helpers/get-error';
import { Basement } from 'api/typings';
import { useAddBasementMutation } from 'api/hooks/basements';
import AddBasementSettings from '../../components/basement/add-basement-settings/add-basement-settings';
import { BASEMENTS_PAGE } from '../../shared/constants';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type AddBasementConnectorProps = {
    onBasementAdded: (id: string) => void;
    initialBasement?: Basement;
};

let initialValues: Basement = {
    name: '',
    id: '',
    supported_args: [],
    gpu_support: false
};

const AddBasementConnector: FC<AddBasementConnectorProps> = ({
    onBasementAdded,
    initialBasement
}) => {
    useEffect(() => {
        if (initialBasement) {
            initialValues = initialBasement;
        } else {
            initialValues = {
                name: '',
                id: '',
                supported_args: [],
                gpu_support: false
            };
        }
    }, []);
    const addBasementMutation = useAddBasementMutation();

    // will be needed in case of more steps in wizard
    // const [stepIndex, setStepIndex] = useState(0);
    // const handleNext = () => {
    //     setStepIndex(stepIndex + 1);
    // };
    // const handlePrev = () => {
    //     setStepIndex(stepIndex - 1);
    // };
    const finishButtonCaption = 'Add Basement';

    const renderForm = useCallback(({ lens, save }: RenderFormProps<Basement>) => {
        const steps: WizardPropsStep[] = [
            {
                title: 'Basement',
                content: (
                    <>
                        <div className={wizardStyles['content__body']}>
                            <AddBasementSettings lens={lens} />
                        </div>
                        <div className={wizardStyles['content__footer']}>
                            {renderWizardButtons({
                                onNextClick: () => {
                                    save();
                                    // handleNext();
                                },
                                nextButtonCaption: finishButtonCaption
                            })}
                        </div>
                    </>
                )
            }
        ];
        return <Wizard steps={steps} returnUrl={BASEMENTS_PAGE} stepIndex={0} />;
    }, []);
    const handleSave = useCallback(async (values: Basement) => {
        try {
            const response = await addBasementMutation.mutateAsync(values);
            values.id = response.id;
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
        (values: Basement) => {
            if (values.id) {
                onBasementAdded(values.id);
            }
        },
        [onBasementAdded]
    );

    return (
        <Form<Basement>
            renderForm={renderForm}
            onSave={handleSave}
            value={{ ...initialValues }}
            onSuccess={handleSuccess}
        />
    );
};

export default AddBasementConnector;
