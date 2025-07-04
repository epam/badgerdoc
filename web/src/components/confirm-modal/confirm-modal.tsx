// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React from 'react';
import {
    ModalBlocker,
    ModalFooter,
    ModalHeader,
    ModalWindow,
    FlexRow,
    Panel,
    ScrollBars,
    Text,
    Button
} from '@epam/loveship';
import { IModal } from '@epam/uui-core';

interface ConfirmModalProps {
    modalProps: IModal<string>;
    confirmationText: string;
}

export const ConfirmModal = ({ modalProps, confirmationText }: ConfirmModalProps) => (
    <ModalBlocker {...modalProps} blockerShadow="dark">
        <ModalWindow>
            <Panel>
                <ModalHeader title="Attention" onClose={() => modalProps.abort()} />
                <ScrollBars hasTopShadow hasBottomShadow>
                    <FlexRow padding="24">
                        <Text size="36">{confirmationText}</Text>
                    </FlexRow>
                </ScrollBars>
                <ModalFooter>
                    <Button
                        fill="white"
                        color="sky"
                        caption="Cancel"
                        onClick={() => modalProps.abort()}
                    />
                    <Button
                        color="sky"
                        caption="Confirm"
                        onClick={() => modalProps.success('Success action')}
                    />
                </ModalFooter>
            </Panel>
        </ModalWindow>
    </ModalBlocker>
);
