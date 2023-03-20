import { useState, useRef, RefObject } from 'react';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { Annotation, Point, Bound } from '..';
import { useMouseEvents } from './use-mouse-events';

type UseAnnotationMoveHook = (params: AnnotationMoveParams) => AnnotationMoveResult;

type AnnotationMoveParams = {
    selectedAnnotation?: Annotation;
    panoRef: RefObject<HTMLDivElement>;
    selectedAnnotationRef: RefObject<HTMLDivElement>;
    isEditable?: boolean;
};

type AnnotationMoveResult = {
    coords: Point[];
    isEnded: boolean | null;
};

export const ANNOTATION_LABEL_CLASS = 'js-label';

export const useAnnotationMove: UseAnnotationMoveHook = ({
    panoRef,
    selectedAnnotationRef,
    selectedAnnotation,
    isEditable
}) => {
    const [coords, setCoords] = useState<Point[]>([]);
    const [isEnded, setIsEnded] = useState<boolean>(false);

    const selectedAnnotationCoords = useRef<Point[]>([]);

    const getCoords = (bound: Bound) => {
        return [
            { x: bound.x, y: bound.y },
            { x: bound.x + bound.width, y: bound.y + bound.height }
        ];
    };

    useMouseEvents({
        ref: panoRef,
        onMouseDown(_, target: HTMLElement) {
            if (!isEditable) return;
            if (!target.classList.contains(ANNOTATION_LABEL_CLASS)) {
                setCoords([]);
                return;
            }

            if (selectedAnnotation) {
                const newCoords = getCoords(selectedAnnotation.bound);
                selectedAnnotationCoords.current = newCoords;
                setCoords(newCoords);
            }

            setIsEnded(false);
        },
        onMouseMove: (start: Point, end: Point, target: HTMLElement) => {
            if (!isEditable) return;

            if (
                !target.classList.contains(ANNOTATION_LABEL_CLASS) ||
                !selectedAnnotation ||
                target.id !== `${ANNOTATION_FLOW_ITEM_ID_PREFIX}${selectedAnnotation.id}` // make sure we hovered label of selected annotation, not any other
            ) {
                return false;
            }

            const xDelta = end.x - start.x;
            const yDelta = end.y - start.y;

            let { x, y } = selectedAnnotationCoords.current[0];

            x += xDelta;
            y += yDelta;

            const newCoords = [
                { x: x, y: y },
                { x: x + selectedAnnotation.bound.width, y: y + selectedAnnotation.bound.height }
            ];

            setCoords(newCoords);
            moveAnnotation({ x, y });
        },
        onMouseUp(_, __, target: HTMLElement) {
            if (!isEditable) return;

            if (!target.classList.contains(ANNOTATION_LABEL_CLASS)) return;

            setIsEnded(true);
        }
    });

    const moveAnnotation = (coords: Point) => {
        const element = selectedAnnotationRef.current!;
        element.style.left = coords.x + 'px';
        element.style.top = coords.y + 'px';
    };

    return isEditable ? { coords, isEnded } : { coords: [], isEnded: null };
};
