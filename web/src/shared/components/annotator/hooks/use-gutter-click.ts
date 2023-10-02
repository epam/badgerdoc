// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { RefObject, useCallback } from 'react';
import { Annotation, Maybe, Point, TableGutter, TableGutterMap } from '../typings';
import { getRefOffset } from '../utils/get-ref-offset';
import { isPointInsideRect } from '../utils/is-intersected';
import { gutterToRect } from '../utils/gutter-to-rect';

export const useGutterClick = (
    panoRef: RefObject<HTMLDivElement>,
    annotation: Annotation,
    selectedAnnotation: Maybe<Annotation>,
    guttersMap: TableGutterMap,
    scale: number,
    setGutter: (g: Maybe<TableGutter>) => void
) => {
    return useCallback(
        (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
            const { offsetLeft, offsetTop } = getRefOffset(panoRef);
            const { bound } = annotation;

            const clickPoint = {
                x: (e.pageX - offsetLeft) / scale,
                y: (e.pageY - offsetTop) / scale
            } as Point;
            if (guttersMap) setGutter(undefined);
            const affectedGutters = Object.values(guttersMap).filter((gutter) => {
                const gutterRect = gutterToRect(bound, gutter, scale);
                return isPointInsideRect(gutterRect, clickPoint);
            })[0];
            setGutter(selectedAnnotation ? affectedGutters : undefined); //It's fine if we set it to undefined
        },
        [
            guttersMap,
            Object.values(guttersMap).length,
            setGutter,
            scale,
            panoRef,
            panoRef.current,
            selectedAnnotation
        ]
    );
};
