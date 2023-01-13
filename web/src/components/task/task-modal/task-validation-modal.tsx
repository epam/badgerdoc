import React, { FC, ReactNode, useState } from 'react';
import {
    FormSaveResponse,
    IModal,
    Metadata,
    IFormApi,
    useUuiContext,
    useArrayDataSource
} from '@epam/uui';
import {
    ModalBlocker,
    ModalWindow,
    ModalHeader,
    FlexRow,
    LabeledInput,
    Button,
    ModalFooter,
    Panel,
    FlexCell,
    Form,
    Text,
    ControlWrapper,
    RadioGroup,
    PickerInput
} from '@epam/loveship';
import styles from './task-modal.module.scss';
import { User } from '../../../api/typings';

export interface TaskValidationValues {
    option_invalid?: string;
    option_edited?: string;
}
interface IProps extends IModal<TaskValidationValues> {
    onSaveForm: (
        formOption: TaskValidationValues
    ) => Promise<FormSaveResponse<TaskValidationValues> | void>;
    allValid: boolean;
    invalidPages: number;
    editedPageCount: number;
    validSave: () => void;
    allUsers: {
        owners: User[];
        annotators: User[];
        validators: User[];
    };
    currentUser: string;
    isOwner: boolean;
}

export const FinishTaskValidationModal: FC<IProps> = (modalProps) => {
    const svc = useUuiContext();
    const [validatorUserId, onValidatorUserIdChange] = useState(
        modalProps.allUsers.validators[0]?.id || modalProps.allUsers.annotators[0]?.id
    );
    const [annotatorUserId, onAnnotatorUserIdChange] = useState(
        modalProps.allUsers.annotators[0]?.id
    );

    const handleLeave = () => svc.uuiLocks.acquire(() => Promise.resolve());
    const [formOption] = useState<TaskValidationValues>({
        option_invalid: '',
        option_edited: ''
    });

    const annotatorsDataSource = useArrayDataSource<User, string, any>(
        {
            items: modalProps.allUsers.annotators ?? []
        },
        []
    );

    const getMetaData = (): Metadata<TaskValidationValues> => ({
        props: {
            option_invalid: { isRequired: true },
            option_edited: { isRequired: true }
        }
    });

    const renderForm = ({ lens, save }: IFormApi<TaskValidationValues>): ReactNode => {
        return (
            <>
                <Panel>
                    {modalProps.invalidPages && (
                        <>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput
                                        label={`Validation of invalid pages (${modalProps.invalidPages})`}
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
                    {modalProps.editedPageCount !== 0 && (
                        <>
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput
                                        label={`Validation of edited pages (${modalProps.editedPageCount})`}
                                        {...lens.prop('option_edited').toProps()}
                                    >
                                        <ControlWrapper size="36">
                                            <RadioGroup
                                                items={[
                                                    {
                                                        id: 'not_required',
                                                        name: `Does not required`,
                                                        isDisabled: !modalProps.isOwner
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
                        onClick={() => handleLeave().then(modalProps.abort)}
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
        <ModalBlocker
            blockerShadow="dark"
            {...modalProps}
            abort={() => handleLeave().then(modalProps.abort)}
        >
            <ModalWindow>
                <Panel background="white">
                    <ModalHeader title="Asign" onClose={modalProps.abort} />

                    {modalProps.allValid && (
                        <>
                            <FlexRow padding="24">
                                <Text size="36"> {'All pages valid'} </Text>
                            </FlexRow>
                            <ModalFooter>
                                <Button
                                    fill="white"
                                    caption="Cancel"
                                    onClick={() => modalProps.abort()}
                                />
                                <Button
                                    caption="Confirm validation"
                                    size={'36'}
                                    onClick={async () => {
                                        await modalProps.validSave();
                                        modalProps.success({ option_invalid: '' });
                                    }}
                                />
                            </ModalFooter>
                        </>
                    )}
                    {!modalProps.allValid && (
                        <Form<TaskValidationValues>
                            value={formOption}
                            onSave={modalProps.onSaveForm}
                            onSuccess={(formOption) => modalProps.success(formOption)}
                            renderForm={renderForm}
                            getMetadata={getMetaData}
                        />
                    )}
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
