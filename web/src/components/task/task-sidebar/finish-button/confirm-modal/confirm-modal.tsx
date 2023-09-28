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

export const ConfirmModal = (modalProps: IModal<string>) => (
    <ModalBlocker {...modalProps} blockerShadow="dark">
        <ModalWindow>
            <Panel>
                <ModalHeader title="Attention" onClose={() => modalProps.abort()} />
                <ScrollBars hasTopShadow hasBottomShadow>
                    <FlexRow padding="24">
                        <Text size="36">Are you sure you want to stop annotating this document?</Text>
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
