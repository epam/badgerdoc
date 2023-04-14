import React, { FC } from 'react';
import { FlexRow, IconButton, Text } from '@epam/loveship';
import { Label } from 'api/typings';

import { ReactComponent as crossIcon } from '@epam/assets/icons/common/navigation-close-18.svg';
import styles from './styles.module.scss';

export const LabelRow: FC<{
    label: Label;
    isOwner: boolean;
    isEditable: boolean;
    onClick: (label: Label) => void;
    onDelete: (label: Label) => void;
}> = ({ label, isEditable, isOwner, onClick, onDelete }) => {
    const handleClick = () => {
        onClick(label);
    };
    const handleDelete = () => {
        onDelete(label);
    };

    return (
        <FlexRow cx={styles.labelRow} onClick={isOwner ? undefined : handleClick}>
            <Text cx={styles.labelText}>{label.name}</Text>
            {isEditable && (
                <IconButton
                    icon={crossIcon}
                    onClick={(event) => {
                        event.stopPropagation();
                        handleDelete();
                    }}
                />
            )}
        </FlexRow>
    );
};
