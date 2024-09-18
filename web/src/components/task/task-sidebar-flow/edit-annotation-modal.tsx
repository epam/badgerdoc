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
    few_shot_learning?: boolean | undefined;
}

export const EditAnnotationModal: FC<any> = ({
    abort,
    handleAnnotationChange,
    annotationValues,
    ...modalProps
}) => {
    const { lens, save } = useForm<EditAnnotation>({
        value: {
            text: annotationValues.text,
            comment: annotationValues.comment,
            few_shot_learning: annotationValues.few_shot_learning
        },
        onSave: (value) => {
            handleAnnotationChange(value);
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
                                    label="Few-shot-learning"
                                    {...lens.prop('few_shot_learning').toProps()}
                                    cx={styles.fewShotLearning}
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
