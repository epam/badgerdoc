import noop from 'lodash/noop';
import { IconButton } from '@epam/loveship';
import React from 'react';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import styles from './text-label.module.scss';

type TextLabelProps = {
    color: string;
    className: string;
    label?: React.ReactNode;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    isEditable?: boolean;
    isSelected?: boolean;
    isHovered?: boolean;
    taskHasTaxonomies?: boolean;
};

export const TextLabel = ({
    color,
    className,
    label,
    onCloseIconClick = noop,
    onContextMenu = noop,
    isEditable,
    isSelected,
    isHovered,
    taskHasTaxonomies
}: TextLabelProps) => {
    const labelStyle = isSelected || isHovered || taskHasTaxonomies ? styles.show : '';
    return (
        <span
            className={`${className} ${labelStyle}`}
            style={{ backgroundColor: color }}
            onContextMenu={onContextMenu}
        >
            {label}
            {isEditable && (
                <IconButton
                    icon={closeIcon}
                    onClick={onCloseIconClick}
                    color={'white'}
                    iconPosition={'right'}
                />
            )}
        </span>
    );
};
