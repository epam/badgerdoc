// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, eqeqeq */
import React, { Fragment, useMemo } from 'react';
import noop from 'lodash/noop';

import { stringToRGBA } from '../../utils/string-to-rgba';
import { createBoundsFromTokens, getBorders, TextAnnotationProps } from './helpers';
import { getAnnotationElementId } from '../../utils/use-annotation-links';
import { TextLabel } from '../text-label';
import styles from './text-annotation.module.scss';

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
    isHovered
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
                                        <TextLabel
                                            id={id}
                                            className={styles[`text-annotation-label-end`]}
                                            isEditable={isEditable}
                                            isSelected={isSelected}
                                            isHovered={isHovered}
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
                                            label={annLabel.label}
                                            color={annLabel.color ?? color}
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
