import noop from 'lodash/noop';
import React, { RefObject } from 'react';
import { Bound } from '../../typings';
import styles from './box-annotation.module.scss';
import { IconButton } from '@epam/loveship';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { getAnnotationElementId } from '../../utils/use-annotation-links';
import { ANNOTATION_LABEL_CLASS } from '../../hooks/use-annotation-move';

type BoxAnnotationProps = {
    label?: React.ReactNode;
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
    taskHasTaxonomies?: boolean;
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
    boundType,
    onMouseEnter = noop,
    onMouseLeave = noop,
    taskHasTaxonomies
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

    const annotationClassNames = `${styles.annotation} ${
        isSelected ? styles.selected : isHovered || taskHasTaxonomies ? styles.hovered : ''
    }`;
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
                data-id={id}
            >
                {label}
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

const Resizer = ({ color }: { color: string }) => (
    <>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-left']} resizer top-left`}
        ></div>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-right']} resizer top-right`}
        ></div>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-left']} resizer bottom-left`}
        ></div>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-right']} resizer bottom-right`}
        ></div>
    </>
);
