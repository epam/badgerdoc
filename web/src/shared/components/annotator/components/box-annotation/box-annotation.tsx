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
        left: x,
        top: y,
        width: width,
        height: height,
        border: `2px ${color} solid`,
        color: color,
        zIndex: isSelected ? 10 : 1
    };

    const annotationClassNames = cx(styles.annotation, {
        [styles.selected]: isSelected || isHovered
    });

    return (
        <div
            role="none"
            onClick={onClick}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            onMouseEnter={onMouseEnter}
            onMouseLeave={onMouseLeave}
            className={annotationClassNames}
            style={annStyle}
            ref={annotationRef}
            id={getAnnotationElementId(page, id)}
        >
            {isSelected && isEditable && <Resizer color={color} />}
            <span
                className={`${styles.label} ${
                    isEditable && isSelected ? styles.labelDraggable : ''
                } ${ANNOTATION_LABEL_CLASS}`}
                style={{ backgroundColor: color }}
                id={`${ANNOTATION_LABEL_ID_PREFIX}${id}`}
            >
                {label.split('.').pop()}
                {isEditable && (
                    <IconButton
                        icon={closeIcon}
                        cx={styles.close}
                        onClick={onCloseIconClick}
                        color={'white'}
                        iconPosition={'right'}
                    />
                )}
            </span>
        </div>
    );
};

export const ANNOTATION_RESIZER_CLASS = 'resizer';

const Resizer = ({ color }: { color: string }) => (
    <>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-left']} ${ANNOTATION_RESIZER_CLASS} top-left`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-right']} ${ANNOTATION_RESIZER_CLASS} top-right`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-left']} ${ANNOTATION_RESIZER_CLASS} bottom-left`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-right']} ${ANNOTATION_RESIZER_CLASS} bottom-right`}
        />
    </>
);
