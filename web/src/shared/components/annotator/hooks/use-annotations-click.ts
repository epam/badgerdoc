import React, { RefObject, useCallback } from 'react';
import { AnnotationImageToolType, AnnotationLinksBoundType } from 'shared';
import { Annotation, AnnotationBoundType, Point } from '../typings';
import { getRefOffset } from '../utils/get-ref-offset';
import { isPointInsideRect } from '../utils/is-intersected';
import { scaleAnnotation } from '../utils/scale-annotation';
import { annotationToRect, tokenToRect } from '../utils/to-rect-utils';

const square = (ann: Annotation) => ann.bound.width * ann.bound.height;

export const useAnnotationsClick = (
    panoRef: RefObject<HTMLDivElement>,
    annotations: Annotation[],
    scale: number,
    allowedSelectionTypes: Array<
        AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
    >,
    setSelectedAnnotation: (ann: Annotation | undefined) => void,
    unselectAnnotation: () => void
) => {
    return useCallback(
        (e: React.MouseEvent<HTMLDivElement, MouseEvent>, original?: Annotation) => {
            const { offsetLeft, offsetTop } = getRefOffset(panoRef);

            const clickPoint = {
                x: (e.pageX - offsetLeft) / scale,
                y: (e.pageY - offsetTop) / scale
            } as Point;

            const affectedAnnotations = annotations.filter((annotation) => {
                if (annotation.boundType === 'text') {
                    const annTokensInClick = annotation?.tokens?.filter((token) =>
                        isPointInsideRect(tokenToRect(token), clickPoint)
                    );
                    return annTokensInClick?.length !== 0 ? annotation : null;
                }
                return isPointInsideRect(annotationToRect(annotation), clickPoint);
            });

            const smallestClickedAnn = affectedAnnotations.reduce((a, b) => {
                return square(a) < square(b) ? a : b;
            }, affectedAnnotations[0]);

            if (original) {
                const annotation =
                    !smallestClickedAnn || smallestClickedAnn.id == original?.id
                        ? original
                        : // original one is already scaled
                          scaleAnnotation(smallestClickedAnn, scale);
                if (allowedSelectionTypes.includes(annotation.boundType)) {
                    setSelectedAnnotation(annotation);
                    return;
                }
            }
            if (affectedAnnotations.length === 0) {
                unselectAnnotation();
            }
        },
        [
            annotations,
            annotations.length,
            allowedSelectionTypes,
            setSelectedAnnotation,
            scale,
            panoRef,
            panoRef.current
        ]
    );
};
