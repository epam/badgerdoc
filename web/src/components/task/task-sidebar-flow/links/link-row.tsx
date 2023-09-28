// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import React, { FC } from 'react';
import { FlexRow, IconContainer, Text } from '@epam/loveship';
import { Annotation } from 'shared';

import { ReactComponent as crossIcon } from '@epam/assets/icons/common/navigation-close-18.svg';

import styles from './styles.module.scss';

export const LinkRow: FC<{
    to: Annotation['id'];
    onDelete: () => void;
    annotationName: string;
    onClose?: () => void;
    isEditable: boolean;
    onSelect: (id: Annotation['id']) => void;
    icon: React.FunctionComponent<
        React.SVGProps<SVGSVGElement> & {
            title?: string | undefined;
        }
    >;
}> = ({ onClose, onSelect, onDelete, to, annotationName, icon, isEditable }) => (
    <FlexRow
        cx={styles['link-row']}
        onClick={(event) => {
            event.stopPropagation();
            onSelect(to);
            onClose?.();
        }}
    >
        <div className={styles.title}>
            <IconContainer icon={icon} color="cobalt" />
            <Text>{annotationName}</Text>
        </div>
        {isEditable && (
            <IconContainer
                cx={styles['cross']}
                icon={crossIcon}
                onClick={(event) => {
                    event.stopPropagation();
                    onDelete();
                }}
            />
        )}
    </FlexRow>
);
