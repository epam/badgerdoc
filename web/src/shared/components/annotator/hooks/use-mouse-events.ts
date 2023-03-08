import React, { useRef, useEffect } from 'react';
import noop from 'lodash/noop';
import { Point } from '..';
import { getRefOffset } from '../utils/get-ref-offset';
import isClick from '../utils/is-click';
import { possiblyClickedOnTableGutter } from '../utils/detect-gutter-click';

type UseMouseEventsParams = {
    ref: React.RefObject<HTMLDivElement>;
    onMouseDown: (start: Point, target: HTMLElement) => void;
    onMouseMove: (start: Point, end: Point, target: HTMLElement) => void;
    onMouseUp: (start: Point, end: Point, target: HTMLElement) => void;
    onClick?: (start: Point) => void;
};

export const useMouseEvents = ({
    ref,
    onMouseDown,
    onMouseMove,
    onMouseUp,
    onClick = noop
}: UseMouseEventsParams) => {
    const target = useRef<HTMLElement | null>();
    const start = useRef<Point>();
    const end = useRef<Point>();
    const mouseDown = useRef(false);
    const handlers = useRef({
        onMouseDown,
        onMouseMove,
        onMouseUp,
        onClick
    });
    handlers.current = { onMouseDown, onMouseMove, onMouseUp, onClick };

    const getPanoCoords = (pageX: number, pageY: number): Point => {
        const { offsetLeft, offsetTop } = getRefOffset(ref);

        return {
            x: pageX - offsetLeft,
            y: pageY - offsetTop
        };
    };

    const handleMouseDown = (e: MouseEvent) => {
        if (e.button !== 0) {
            return;
        }
        if (possiblyClickedOnTableGutter(e.target as HTMLElement)) {
            e.preventDefault();
        }

        mouseDown.current = true;
        target.current = e.target as HTMLElement;
        start.current = getPanoCoords(e.pageX, e.pageY);
        end.current = start.current;
        handlers.current.onMouseDown(start.current, target.current);
    };

    const handleMouseMove = (e: MouseEvent) => {
        if (!mouseDown.current) {
            return;
        }
        if (possiblyClickedOnTableGutter(e.target as HTMLElement)) {
            e.preventDefault();
        }
        end.current = getPanoCoords(e.pageX, e.pageY);
        if (isClick(start.current!, end.current!)) {
            return;
        }

        handlers.current.onMouseMove(start.current!, end.current!, target.current!);
    };

    const handleMouseUp = () => {
        if (!mouseDown.current) {
            return;
        }
        mouseDown.current = false;
        if (isClick(start.current!, end.current!)) {
            handlers.current.onClick(start.current!);
        } else {
            handlers.current.onMouseUp(start.current!, end.current!, target.current!);
        }
        target.current = null;
    };

    useEffect(() => {
        const el = ref.current;
        if (!el) {
            return;
        }
        el.addEventListener('mousedown', handleMouseDown);
        el.addEventListener('mousemove', handleMouseMove);
        el.addEventListener('mouseup', handleMouseUp);
        return () => {
            el.removeEventListener('mousedown', handleMouseDown);
            el.removeEventListener('mousemove', handleMouseMove);
            el.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);
};
