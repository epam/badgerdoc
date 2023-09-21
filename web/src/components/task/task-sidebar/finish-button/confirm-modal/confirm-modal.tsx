import React from 'react';
import {
    ModalBlocker,
    ModalFooter,
    ModalHeader,
    ModalWindow,
    FlexRow,
    FlexSpacer,
    Panel,
    ScrollBars,
    Text,
    Button
} from '@epam/loveship';
import { IModal } from '@epam/uui-core';
import styles from './comfirm-modal.module.scss';

export const ConfirmModal = (modalProps: IModal<string>) => {
    return (
        <ModalBlocker {...modalProps}>
            <ModalWindow>
                <Panel background="night50" cx={styles['modalBody']}>
                    <ModalHeader title="Attention" onClose={() => modalProps.abort()} />
                    <ScrollBars hasTopShadow hasBottomShadow>
                        <FlexRow padding="24">
                            <Text size="36">Are you sure you want to stop editing?</Text>
                        </FlexRow>
                    </ScrollBars>
                    <ModalFooter>
                        <FlexSpacer />
                        <Button
                            color="fire"
                            fill="white"
                            caption="Cancel"
                            onClick={() => modalProps.abort()}
                        />
                        <Button
                            color="sky"
                            caption="Ok"
                            onClick={() => modalProps.success('Success action')}
                        />
                    </ModalFooter>
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
