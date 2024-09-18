// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
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
    TextArea,
    useForm
} from '@epam/loveship';

import styles from './task-sidebar-flow.module.scss';

interface EditAnnotation {
    text?: string | null;
    comment?: string | null;
    llm_fine_tune?: boolean | null;
}

export const EditAnnotationModal: FC<any> = ({
    abort,
    handleAnnotationTextChange,
    annotationText,
    ...modalProps
}) => {
    const { lens, save } = useForm<EditAnnotation>({
        value: { text: annotationText },
        onSave: (value) => {
            handleAnnotationTextChange(value);
            abort();
            return Promise.resolve({ form: value });
        }
    });

    return (
        <ModalBlocker {...modalProps} abort={abort} blockerShadow="dark">
            <ModalWindow>
                <ModalHeader title="Edit annotation" onClose={abort} />
                <ScrollBars>
                    <Panel>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Text" {...lens.prop('text').toProps()}>
                                    <TextArea
                                        autoSize
                                        {...lens.prop('text').toProps()}
                                        cx={styles.textArea}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <ModalFooter>
                            <FlexSpacer />
                            <Button onClick={abort} caption="Cancel" />
                            <Button caption="Confirm" onClick={save} />
                        </ModalFooter>
                        <FlexSpacer />
                    </Panel>
                </ScrollBars>
            </ModalWindow>
        </ModalBlocker>
    );
};
