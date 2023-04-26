import React from 'react';
import noop from 'lodash/noop';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { IconButton } from '@epam/loveship';
import styles from './text-label.module.scss';
import { cx } from '@epam/uui';
import { getAnnotationLabelColors, isContrastColor } from 'shared/helpers/annotations';

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
        onContextMenu={onContextMenu}
        style={getAnnotationLabelColors(color)}
        className={cx(className, { [styles.show]: isSelected || isHovered })}
    >
        {label?.split('.').pop()}
        {isEditable && (
            <IconButton
                icon={closeIcon}
                iconPosition={'right'}
                onClick={onCloseIconClick}
                color={isContrastColor(color) ? 'white' : 'night900'}
            />
        )}
    </span>
);
