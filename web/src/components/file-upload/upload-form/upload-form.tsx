import React, { FC } from 'react';
import { Button, Text, Panel } from '@epam/loveship';
import { DropSpot, UploadFileToggler } from '@epam/uui-components';
import { DropZone } from '../drop-zone/drop-zone';

import { ReactComponent as Image } from './icon.svg';

import styles from './upload-form.module.scss';

type UploadFormProps = {
    onFilesAdded: (files: File[]) => void;
};

export const UploadForm: FC<UploadFormProps> = ({ onFilesAdded }) => {
    return (
        <Panel cx={`${styles['upload-form']}`}>
            <DropSpot
                onFilesDropped={onFilesAdded}
                render={({ eventHandlers: { onDragEnter, onDrop, onDragLeave, onDragOver } }) => (
                    <DropZone
                        onDragEnter={onDragEnter}
                        onDrop={onDrop}
                        onDragLeave={onDragLeave}
                        onDragOver={onDragOver}
                    >
                        <Image></Image>
                        <Text
                            // it should be h4, that has styles exact to UI specification
                            font="sans-semibold"
                            fontSize="18"
                            lineHeight="24"
                            cx={styles['upload-form__drop-zone__text']}
                        >
                            Drag File Here
                        </Text>
                        <Text
                            // it should be p tag, that has styles exact to UI specification
                            fontSize="14"
                            font="sans"
                            lineHeight="24"
                            cx={styles['upload-form__drop-zone__text']}
                        >
                            <UploadFileToggler
                                onFilesAdded={onFilesAdded}
                                render={({ onClick }) => (
                                    <Text
                                        // it should be p tag, that has styles exact to UI specification
                                        fontSize="14"
                                        font="sans"
                                        lineHeight="24"
                                        cx={styles['upload-form__drop-zone__text']}
                                    >
                                        or{' '}
                                        <Button
                                            caption="browse"
                                            fill="light"
                                            cx={styles['upload-form__drop-zone__text__button']}
                                            onClick={onClick}
                                        />{' '}
                                        files from your device
                                    </Text>
                                )}
                            ></UploadFileToggler>
                        </Text>
                    </DropZone>
                )}
            ></DropSpot>
        </Panel>
    );
};
