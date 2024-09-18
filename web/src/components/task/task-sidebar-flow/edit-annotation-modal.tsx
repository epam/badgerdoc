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
    Button,
    ScrollBars,
    ModalFooter,
    Panel,
    FlexCell,
    TextArea,
    useForm,
    Checkbox
} from '@epam/loveship';

import styles from './task-sidebar-flow.module.scss';

export interface EditAnnotation {
    text?: string | undefined;
    comment?: string | undefined;
    llm_fine_tune?: boolean | undefined;
}

export const EditAnnotationModal: FC<any> = ({
    abort,
    handleAnnotationTextChange,
    annotationValues,
    ...modalProps
}) => {
    const { lens, save } = useForm<EditAnnotation>({
        value: {
            text: annotationValues.text,
            comment: annotationValues.comment,
            llm_fine_tune: annotationValues.llm_fine_tune
        },
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
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Comment" {...lens.prop('comment').toProps()}>
                                    <TextArea
                                        autoSize
                                        {...lens.prop('comment').toProps()}
                                        cx={styles.textArea}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <Checkbox
                                    label="LLM fine-tune"
                                    {...lens.prop('llm_fine_tune').toProps()}
                                    cx={styles.fineTune}
                                />
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
