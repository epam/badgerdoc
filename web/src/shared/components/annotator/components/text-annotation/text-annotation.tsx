import noop from 'lodash/noop';
import React, { Fragment, useMemo } from 'react';
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
    label,
    onCloseIconClick = noop,
    onContextMenu = noop,
    isEditable,
    isSelected,
    isHovered,
    taskHasTaxonomies
}: TextAnnotationLabelProps) => {
    return (
        <TextLabel
            className={styles[`text-annotation-label-end`]}
            isEditable={isEditable}
            isSelected={isSelected}
            isHovered={isHovered}
            onCloseIconClick={onCloseIconClick}
            onContextMenu={onContextMenu}
            label={label}
            color={color}
            taskHasTaxonomies={taskHasTaxonomies}
        />
    );
};

export const TextAnnotation = ({
    label = '',
    color = 'black',
    id = '',
    labels = [
        {
            annotationId: id,
            color: color,
            label: label
        }
    ],
    tokens,
    onClick = noop,
    onContextMenu = noop,
    onAnnotationContextMenu = noop,
    onAnnotationDelete = noop,
    onDoubleClick = noop,
    onMouseEnter = noop,
    onMouseLeave = noop,
    scale,
    isEditable,
    isSelected,
    page,
    isHovered,
    taskHasTaxonomies
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
                        <div className={styles.annLabel}>
                            {singleBound.params.labelPosition != 'no_label' &&
                                labels.map((annLabel) => (
                                    <Fragment key={annLabel.annotationId}>
                                        <TextAnnotationLabel
                                            color={annLabel.color ?? color}
                                            labelPosition="end"
                                            label={annLabel.label}
                                            onCloseIconClick={() => {
                                                onAnnotationDelete(annLabel.annotationId!);
                                            }}
                                            onContextMenu={(e) => {
                                                e.stopPropagation();
                                                e.preventDefault();
                                                onAnnotationContextMenu(
                                                    e,
                                                    annLabel.annotationId!,
                                                    labels
                                                );
                                            }}
                                            isEditable={isEditable}
                                            isSelected={isSelected}
                                            isHovered={isHovered}
                                            taskHasTaxonomies={taskHasTaxonomies}
                                        />
                                    </Fragment>
                                ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
