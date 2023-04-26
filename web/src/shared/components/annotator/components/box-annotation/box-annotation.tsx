import React, { RefObject } from 'react';

import noop from 'lodash/noop';

import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { IconButton } from '@epam/loveship';

import { ANNOTATION_LABEL_CLASS } from '../../hooks/use-annotation-move';
import { Bound } from '../../typings';
import { getAnnotationElementId } from '../../utils/use-annotation-links';
import styles from './box-annotation.module.scss';
import { cx } from '@epam/uui';
import { ANNOTATION_LABEL_ID_PREFIX } from 'shared/constants/annotations';
import { getAnnotationLabelColors, isContrastColor } from 'shared/helpers/annotations';
import { Resizer } from './resizer';

type BoxAnnotationProps = {
    label?: string;
    color?: string;
    bound: Bound;
    isSelected?: boolean;
    isEditable?: boolean;
    isHovered?: boolean;
    annotationRef?: RefObject<HTMLDivElement>;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
    onDoubleClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    id: number | string;
    page: number;
    boundType: string;
    onMouseEnter?: React.MouseEventHandler<HTMLDivElement>;
    onMouseLeave?: React.MouseEventHandler<HTMLDivElement>;
};

export const BoxAnnotation = ({
    label = '',
    color = 'black',
    bound,
    isSelected,
    isEditable,
    isHovered,
    annotationRef,
    onClick = noop,
    onDoubleClick = noop,
    onContextMenu = noop,
    onCloseIconClick = noop,
    id,
    page,
    onMouseEnter = noop,
    onMouseLeave = noop
}: BoxAnnotationProps) => {
    const { x, y, width, height } = bound;

    const annStyle = {
        width,
        color,
        height,
        top: y,
        left: x,
        border: `2px ${color} solid`,
        zIndex: isSelected || isHovered ? 10 : 1
    };

    const annotationLabelClassNames = cx(styles.label, ANNOTATION_LABEL_CLASS, {
        [styles.labelDraggable]: isEditable && isSelected
    });

    return (
        <div
            role="none"
            style={annStyle}
            onClick={onClick}
            ref={annotationRef}
            onMouseEnter={onMouseEnter}
            onMouseLeave={onMouseLeave}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            className={styles.annotation}
            id={getAnnotationElementId(page, id)}
        >
            {isSelected && isEditable && <Resizer color={color} />}
            {(isSelected || isHovered) && (
                <span
                    className={annotationLabelClassNames}
                    style={getAnnotationLabelColors(color)}
                    id={`${ANNOTATION_LABEL_ID_PREFIX}${id}`}
                >
                    {label.split('.').pop()}
                    {isEditable && (
                        <IconButton
                            icon={closeIcon}
                            cx={styles.close}
                            iconPosition={'right'}
                            onClick={onCloseIconClick}
                            color={isContrastColor(color) ? 'white' : 'night900'}
                        />
                    )}
                </span>
            )}
        </div>
    );
};

export const ANNOTATION_RESIZER_CLASS = 'resizer';
