import React from 'react';
import noop from 'lodash/noop';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { IconButton } from '@epam/loveship';
import styles from './text-label.module.scss';
import { cx } from '@epam/uui';

type TextLabelProps = {
    color: string;
    className: string;
    label?: string;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    isEditable?: boolean;
    isSelected?: boolean;
    isHovered?: boolean;
};

export const TextLabel = ({
    color,
    className,
    label,
    onCloseIconClick = noop,
    onContextMenu = noop,
    isEditable,
    isSelected,
    isHovered
}: TextLabelProps) => (
    <span
        style={{ backgroundColor: color }}
        onContextMenu={onContextMenu}
        className={cx(className, { [styles.show]: isSelected || isHovered })}
    >
        {label?.split('.').pop()}
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
