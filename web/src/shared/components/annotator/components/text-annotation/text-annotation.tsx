import React, { Fragment, useMemo } from 'react';
import noop from 'lodash/noop';

import { stringToRGBA } from '../../utils/string-to-rgba';
import {
    createBoundsFromTokens,
    getBorders,
    TextAnnotationLabelProps,
    TextAnnotationProps
} from './helpers';
import { getAnnotationElementId } from '../../utils/use-annotation-links';
import { TextLabel } from '../text-label';
import styles from './text-annotation.module.scss';

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
            color,
            label
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
    const isActive = isSelected || isHovered;

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
                const {
                    bound: { width, height, y, x }
                } = singleBound;

                return (
                    <div
                        key={index}
                        className={styles.textAnnotation}
                        style={{
                            background: stringToRGBA(color, isActive ? 0.4 : 0.2),
                            position: 'absolute',
                            width: (width ?? 0) * scale,
                            height: (height ?? 0) * scale,
                            top: (y ?? 0) * scale,
                            left: (x ?? 0) * scale,
                            boxShadow: getBorders(singleBound, color),
                            zIndex: isSelected ? 10 : 1,
                            borderBottom: isActive ? `2px solid ${color}` : 'unset'
                        }}
                    >
                        <div className={styles.annLabel} key={`div-${index}`}>
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
                                            onContextMenu={(event) => {
                                                event.stopPropagation();
                                                event.preventDefault();
                                                onAnnotationContextMenu(
                                                    event,
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
