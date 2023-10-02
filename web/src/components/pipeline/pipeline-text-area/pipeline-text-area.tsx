// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, @typescript-eslint/no-unused-vars */
import { TextArea, Text } from '@epam/loveship';
import React, { FC, useState } from 'react';
import { ReactComponent as EditIcon } from '@epam/assets/icons/common/content-edit-12.svg';
import { ReactComponent as Close } from '@epam/assets/icons/common/navigation-close-12.svg';
import styles from './pipeline-text-area.module.scss';

type PipelineTextAreaProps = {
    text: string;
    onTextChange?: any;
    title: string;
};

export const PipelineTextArea: FC<PipelineTextAreaProps> = ({ text, onTextChange, title }) => {
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [isExpanded, setIsExpanded] = useState<boolean>(false);

    const isReadOnly = !onTextChange;

    return (
        <div className={styles['text-area-wrapper']}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
                <Text fontSize="14" lineHeight="24" color="night800" font="sans">
                    {title}
                </Text>
                {isReadOnly ? (
                    <></>
                ) : (
                    <EditIcon
                        onClick={() => setIsEditing(true)}
                        style={{ marginLeft: '.5rem', cursor: 'pointer' }}
                        height={13}
                        fill="#6C6F80"
                        width={13}
                    />
                )}
                <Close
                    className={`${styles['text-area-close']} ${
                        isEditing || isExpanded ? styles['text-area-close__open'] : ''
                    }`}
                    onClick={() => {
                        setIsEditing(false);
                        setIsExpanded(false);
                    }}
                    height="13px"
                    width="13px"
                />
            </div>
            {isEditing ? (
                <div
                    className={`${styles['text-area__wrapper']} ${
                        isEditing ? styles['text-area__wrapper_extend'] : ''
                    }`}
                >
                    <TextArea
                        autoSize
                        value={text}
                        onValueChange={onTextChange}
                        isDisabled={!isEditing && isReadOnly}
                    />
                </div>
            ) : (
                <div
                    className={`${styles['text-area-readonly']} ${
                        isExpanded ? styles['text-area-readonly__expanded'] : ''
                    }`}
                >
                    <span>
                        <span>
                            {text && text.length > 80 && !isExpanded ? text.slice(0, 80) : text}
                        </span>
                        {!isExpanded && text && text.length >= 80 ? (
                            <button
                                className={styles['text-area-more']}
                                onClick={() => setIsExpanded(true)}
                            >
                                more...
                            </button>
                        ) : (
                            <></>
                        )}
                    </span>
                </div>
            )}
        </div>
    );
};
