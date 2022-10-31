import { useState, useRef, RefObject } from 'react';
import { Annotation, Rect, Point } from '..';
import { get2PointsFromRect } from '../utils/get-2-points-from-rect';
import { annotationToRect } from '../utils/to-rect-utils';
import { useMouseEvents } from './use-mouse-events';

type UseBoxResizeHook = (params: BoxResizeParams) => BoxResizeResult;

type BoxResizeParams = {
    selectedAnnotation?: Annotation;
    panoRef: RefObject<HTMLDivElement>;
    selectedAnnotationRef: RefObject<HTMLDivElement>;
};

type BoxResizeResult = {
    coords: Point[];
    isEnded: boolean;
    isStarted: boolean;
    rect: Rect | null;
};

export const useBoxResize: UseBoxResizeHook = ({
    panoRef,
    selectedAnnotationRef,
    selectedAnnotation
}) => {
    const [rect, setRect] = useState<Rect | null>(null);
    const [coords, setCoords] = useState<Point[]>([]);
    const [isStarted, setIsStarted] = useState<boolean>(false);
    const [isEnded, setIsEnded] = useState<boolean>(false);

    const selectedAnnotationRect = useRef<Rect>();

    const handleMouseMove = (start: Point, end: Point, target: HTMLElement) => {
        if (!target.classList.contains('resizer') || !selectedAnnotationRect.current) return false;

        const xDelta = end.x - start.x;
        const yDelta = end.y - start.y;

        let { left, right, top, bottom } = selectedAnnotationRect.current;

        if (target.classList.contains('bottom-right')) {
            right += xDelta;
            bottom += yDelta;
        } else if (target.classList.contains('bottom-left')) {
            left += xDelta;
            bottom += yDelta;
        } else if (target.classList.contains('top-left')) {
            left += xDelta;
            top += yDelta;
        } else {
            right += xDelta;
            top += yDelta;
        }

        const newRect = { left, right, top, bottom };

        setRect(newRect);
        setCoords(get2PointsFromRect(newRect));
        resizeElement(newRect);
    };

    useMouseEvents({
        ref: panoRef,
        onMouseDown(_, target: HTMLElement) {
            if (!target.classList.contains('resizer')) {
                setCoords([]);
                return;
            }

            selectedAnnotationRect.current = annotationToRect(selectedAnnotation!);

            setCoords(get2PointsFromRect(selectedAnnotationRect.current));
            setIsStarted(true);
            setIsEnded(false);
        },
        onMouseMove: handleMouseMove,
        onMouseUp(_, __, target: HTMLElement) {
            if (!target.classList.contains('resizer')) return;

            setIsEnded(true);
            setIsStarted(false);
        }
    });

    const resizeElement = (rect: Rect) => {
        const { left, top, right, bottom } = rect;
        const width = right - left;
        const height = bottom - top;
        const element = selectedAnnotationRef.current!;

        element.style.top = top + 'px';
        element.style.left = left + 'px';
        element.style.width = width + 'px';
        element.style.height = height + 'px';
    };

    return { coords, isEnded, isStarted, rect };
};
