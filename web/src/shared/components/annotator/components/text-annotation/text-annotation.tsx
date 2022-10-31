import noop from 'lodash/noop';
import React, { useMemo } from 'react';
import styles from './text-annotation.module.scss';
import { hexToRGBA } from '../../utils/hex-to-rgba';
import {
    createBoundsFromTokens,
    getBorders,
    TextAnnotationLabelProps,
    TextAnnotationProps
} from './helpers';
import { TextLabel } from '../text-label';
import { getAnnotationElementId } from '../../utils/use-annotation-links';

const TextAnnotationLabel = ({
    color,
    labelPosition,
    label,
    onCloseIconClick = noop,
    isEditable,
    isSelected,
    isHovered
}: TextAnnotationLabelProps) => {
    return labelPosition === 'both' ? (
        <>
            <TextLabel
                className={styles['text-annotation-label-start']}
                isEditable={isEditable}
                isSelected={isSelected}
                isHovered={isHovered}
                onCloseIconClick={onCloseIconClick}
                label={label}
                color={color}
            />
            <TextLabel
                className={styles['text-annotation-label-end']}
                isEditable={isEditable}
                isSelected={isSelected}
                isHovered={isHovered}
                onCloseIconClick={onCloseIconClick}
                label={label}
                color={color}
            />
        </>
    ) : (
        <TextLabel
            className={styles[`text-annotation-label-${labelPosition}`]}
            isEditable={isEditable}
            isSelected={isSelected}
            isHovered={isHovered}
            onCloseIconClick={onCloseIconClick}
            label={label}
            color={color}
        />
    );
};

export const TextAnnotation = ({
    label = '',
    color = 'black',
    tokens,
    onClick = noop,
    onContextMenu = noop,
    onCloseIconClick = noop,
    onDoubleClick = noop,
    onMouseEnter = noop,
    onMouseLeave = noop,
    scale,
    isEditable,
    isSelected,
    id = '',
    page,
    isHovered
}: TextAnnotationProps) => {
    const bounds = useMemo(() => createBoundsFromTokens(tokens, scale), [tokens, scale]);

    return (
        <div
            role="none"
            id={getAnnotationElementId(page, id)}
            onClick={onClick}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            onMouseEnter={onMouseEnter}
            onMouseLeave={onMouseLeave}
            className={styles.annotation}
        >
            {bounds.map((singleBound, index) => {
                const { bound } = singleBound;
                return (
                    <div
                        key={index}
                        className={styles.textAnnotation}
                        style={{
                            background: hexToRGBA(color, isSelected || isHovered ? 0.3 : 0.2),
                            position: 'absolute',
                            width: (bound.width ?? 0) * scale,
                            height: (bound.height ?? 0) * scale,
                            top: (bound.y ?? 0) * scale,
                            left: (bound.x ?? 0) * scale,
                            boxShadow: getBorders(singleBound, color),
                            zIndex: isSelected ? 10 : 1
                        }}
                    >
                        <TextAnnotationLabel
                            color={color}
                            labelPosition={singleBound.params.labelPosition}
                            label={label}
                            onCloseIconClick={onCloseIconClick}
                            isEditable={isEditable}
                            isSelected={isSelected}
                            isHovered={isHovered}
                        />
                    </div>
                );
            })}
        </div>
    );
};
