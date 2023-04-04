import React, { FC, ReactNode, useState } from 'react';

import {
    Button,
    ControlWrapper,
    FlexCell,
    FlexRow,
    Form,
    LabeledInput,
    ModalBlocker,
    ModalFooter,
    ModalHeader,
    ModalWindow,
    Panel,
    PickerInput,
    RadioGroup,
    Text
} from '@epam/loveship';
import { FormSaveResponse, IFormApi, IModal, Metadata, useArrayDataSource } from '@epam/uui';

import { TUserShort } from '../../../api/typings';
import styles from './task-modal.module.scss';
import { TJobUsers } from 'api/typings/jobs';

export interface TaskValidationValues {
    option_invalid?: string | null;
    option_edited?: string | null;
}
interface IProps extends IModal<TaskValidationValues> {
    onSaveForm: (
        formOption: TaskValidationValues
    ) => Promise<FormSaveResponse<TaskValidationValues> | void>;
    allValid: boolean;
    invalidPages: number;
    editedPageCount: number;
    validSave: () => void;
    allUsers: TJobUsers;
    isOwner: boolean;
    onRedirectAfterFinish: () => void;
}

export const FinishTaskValidationModal: FC<IProps> = (modalProps) => {
    const {
        allUsers,
        invalidPages,
        editedPageCount,
        allValid,
        isOwner,
        abort,
        validSave,
        success,
        onRedirectAfterFinish,
        onSaveForm
    } = modalProps;

    const [validatorUserId, onValidatorUserIdChange] = useState(
        allUsers.validators[0] || allUsers.annotators[0]?.id
    );
    const [annotatorUserId, onAnnotatorUserIdChange] = useState(allUsers.annotators[0]?.id);

    const [formOption] = useState<TaskValidationValues>({
        option_invalid: null,
        option_edited: null
    });

    const annotatorsDataSource = useArrayDataSource<TUserShort, string, any>(
        {
            items: allUsers.annotators ?? []
        },
        []
    );

    const getMetaData = (): Metadata<TaskValidationValues> => ({
        props: {
            option_invalid: { isRequired: !!invalidPages },
            option_edited: { isRequired: !!editedPageCount }
        }
    });

    const handleConfirmValidation = async () => {
        await validSave();
        success({ option_invalid: null });
        onRedirectAfterFinish();
    };

    const handleSuccess = (formOption: TaskValidationValues) => {
        success(formOption);
        onRedirectAfterFinish();
    };

    const renderForm = ({ lens, save }: IFormApi<TaskValidationValues>): ReactNode => {
        return (
            <>
                <Panel>
                    {!!invalidPages && (
                        <>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput
                                        label={`Validation of invalid pages (${invalidPages})`}
                                        {...lens.prop('option_invalid').toProps()}
                                    >
                                        <ControlWrapper size="36">
                                            <RadioGroup
                                                items={[
                                                    { id: 'initial', name: `Initial annotator` },
                                                    { id: 'auto', name: 'Automatically' },
                                                    {
                                                        id: annotatorUserId,
                                                        name: 'Specific annotator'
                                                    }
                                                ]}
                                                {...lens.prop('option_invalid').toProps()}
                                                direction="vertical"
                                            />
                                        </ControlWrapper>
                                    </LabeledInput>
                                </FlexCell>
                            </FlexRow>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput>
                                        <PickerInput
                                            value={annotatorUserId}
                                            onValueChange={onAnnotatorUserIdChange}
                                            selectionMode="single"
                                            valueType="id"
                                            getName={(user) => user.username}
                                            dataSource={annotatorsDataSource}
                                        />
                                    </LabeledInput>
                                </FlexCell>
                            </FlexRow>
                        </>
                    )}
                    {!!editedPageCount && (
                        <>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput
                                        label={`Validation of edited pages (${editedPageCount})`}
                                        {...lens.prop('option_edited').toProps()}
                                    >
                                        <ControlWrapper size="36">
                                            <RadioGroup
                                                items={[
                                                    {
                                                        id: 'not_required',
                                                        name: `Does not required`,
                                                        isDisabled: !isOwner
                                                    },
                                                    { id: 'auto', name: 'Automatically' },
                                                    {
                                                        id: validatorUserId,
                                                        name: 'Specific validator'
                                                    }
                                                ]}
                                                {...lens.prop('option_edited').toProps()}
                                                direction="vertical"
                                            />
                                        </ControlWrapper>
                                    </LabeledInput>
                                </FlexCell>
                            </FlexRow>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput>
                                        <PickerInput
                                            value={validatorUserId}
                                            onValueChange={onValidatorUserIdChange}
                                            selectionMode="single"
                                            valueType={'id'}
                                            getName={(user) => user.username}
                                            dataSource={annotatorsDataSource}
                                        />
                                    </LabeledInput>
                                </FlexCell>
                            </FlexRow>
                        </>
                    )}
                </Panel>
                <div className={styles['modal-block']}>
                    <Button
                        color="sky"
                        fill="white"
                        onClick={abort}
                        caption="Return to validation"
                    />
                    <Button
                        color="grass"
                        caption="Confirm validation and assigment"
                        onClick={save}
                    />
                </div>
            </>
        );
    };
    return (
        <ModalBlocker blockerShadow="dark" {...modalProps} abort={abort}>
            <ModalWindow>
                <Panel background="white">
                    <ModalHeader title="Assign" onClose={abort} />

                    {allValid && (
                        <>
                            <FlexRow padding="24">
                                <Text size="36"> {'All pages valid'} </Text>
                            </FlexRow>
                            <ModalFooter>
                                <Button fill="white" caption="Cancel" onClick={abort} />
                                <Button
                                    caption="Confirm validation"
                                    size={'36'}
                                    onClick={handleConfirmValidation}
                                />
                            </ModalFooter>
                        </>
                    )}
                    {!allValid && (
                        <Form<TaskValidationValues>
                            value={formOption}
                            onSave={onSaveForm}
                            onSuccess={handleSuccess}
                            renderForm={renderForm}
                            getMetadata={getMetaData}
                        />
                    )}
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
