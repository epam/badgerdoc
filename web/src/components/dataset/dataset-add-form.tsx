// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, ReactNode, useState } from 'react';
import { FormSaveResponse, IModal, Metadata, useUuiContext, IFormApi } from '@epam/uui';
import {
    ModalBlocker,
    ModalWindow,
    FlexSpacer,
    ModalHeader,
    FlexRow,
    LabeledInput,
    TextInput,
    Button,
    ScrollBars,
    ModalFooter,
    Panel,
    FlexCell,
    Form
} from '@epam/loveship';

export interface DatasetValues {
    name: string;
}

interface IProps extends IModal<DatasetValues> {
    onSaveDataset: (dataset: DatasetValues) => Promise<FormSaveResponse<DatasetValues> | void>;
}

export const DatasetAddForm: FC<IProps> = (modalProps) => {
    const svc = useUuiContext();
    const [dataset] = useState<DatasetValues>({ name: '' });

    const getMetaData = (): Metadata<DatasetValues> => ({
        props: {
            name: { isRequired: true }
        }
    });

    const renderForm = ({ lens, save }: IFormApi<DatasetValues>): ReactNode => {
        return (
            <>
                <Panel>
                    <FlexRow padding="24" vPadding="12">
                        <FlexCell grow={1}>
                            <LabeledInput label="Dataset Name" {...lens.prop('name').toProps()}>
                                <TextInput placeholder="Name" {...lens.prop('name').toProps()} />
                            </LabeledInput>
                        </FlexCell>
                    </FlexRow>
                </Panel>
                <ModalFooter>
                    <FlexSpacer />
                    <Button
                        color="sky"
                        fill="white"
                        onClick={() => handleLeave().then(modalProps.abort)}
                        caption="Cancel"
                    />
                    <Button color="sky" caption="Save" onClick={save} />
                </ModalFooter>
            </>
        );
    };

    const handleLeave = () => svc.uuiLocks.acquire(() => Promise.resolve());

    return (
        <ModalBlocker
            {...modalProps}
            abort={() => handleLeave().then(modalProps.abort)}
            blockerShadow="dark"
        >
            <ModalWindow>
                <ModalHeader title="Add dataset" onClose={modalProps.abort} />
                <ScrollBars>
                    <Form<DatasetValues>
                        value={dataset}
                        onSave={modalProps.onSaveDataset}
                        onSuccess={(dataset) => modalProps.success(dataset)}
                        renderForm={renderForm}
                        getMetadata={getMetaData}
                    />
                    <FlexSpacer />
                </ScrollBars>
            </ModalWindow>
        </ModalBlocker>
    );
};
