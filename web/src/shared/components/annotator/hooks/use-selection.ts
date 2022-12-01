import React, { useState } from 'react';
import { AnnotationBoundType, AnnotationImageToolType, Point } from '../typings';
import { useMouseEvents } from './use-mouse-events';
import { possiblyClickedOnTableGutter } from '../utils/detect-gutter-click';
import { AnnotationLinksBoundType } from 'shared';

import { ANNOTATION_LABEL_CLASS } from './use-annotation-move';

type SelectionResult = {
    coords: Point[];
    isStarted: boolean;
    isEnded: boolean;
};

export const useSelection = (
    panoRef: React.RefObject<HTMLDivElement>,
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType,
    isCellMode: boolean,
    isEditable: boolean
): SelectionResult => {
    const [coords, setCoords] = useState<Point[]>([]);
    const [isStarted, setIsStarted] = useState<boolean>(false);
    const [isEnded, setIsEnded] = useState<boolean>(false);

    const isClickedOnControlElement = (target: HTMLElement): boolean => {
        return (
            target.classList.contains('resizer') ||
            target.classList.contains(ANNOTATION_LABEL_CLASS) ||
            possiblyClickedOnTableGutter(target) ||
            isCellMode
        );
    };

    useMouseEvents({
        ref: panoRef,
        onMouseDown(_, target) {
            if (['Chain', 'All to all'].includes(selectionType)) return false;
            if (isClickedOnControlElement(target)) return false;
            setCoords([]);
            setIsStarted(true);
            setIsEnded(false);
        },
        onMouseMove(start: Point, end: Point, target) {
            if (['Chain', 'All to all'].includes(selectionType)) return false;
            if (isClickedOnControlElement(target)) return false;
            // HERE WILL BE THE LOGIC ABOUT DIFFERENT SELECTION TYPES
            // WE WILL SET COORDS DIFFERETLY BASED ON TYPE
            setCoords([start, end]);
        },
        onMouseUp() {
            if (['Chain', 'All to all'].includes(selectionType)) return false;
            setIsEnded(true);
            setIsStarted(false);
        },
        //TODO: There is no way just yet for click handling. I believe that when two events fire that quickly (onMouseDown -> onMouseUp)
        //TODO: async-based useState just can't handle two state changes so isEnded is never 'true'
        onClick() {
            setIsEnded(true);
        }
    });
    if (['Chain', 'All to all'].includes(selectionType)) return { coords, isStarted, isEnded };

    return isEditable
        ? { coords, isStarted, isEnded }
        : { coords: [{ x: 0, y: 0 } as Point], isStarted, isEnded: false };
};
