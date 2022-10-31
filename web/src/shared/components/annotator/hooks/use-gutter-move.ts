import { useState, RefObject } from 'react';
import {
    Annotation,
    Point,
    GutterPosition,
    TableGutter,
    GutterType,
    TableGutterMap,
    Maybe,
    GutterPart
} from '..';
import { useMouseEvents } from './use-mouse-events';
import { possiblyClickedOnTableGutter } from '../utils/detect-gutter-click';
type UseGutterMoveHook = (params: GutterMoveParams) => void;

type GutterMoveParams = {
    panoRef: RefObject<HTMLDivElement>;
    selectedGutter: Maybe<TableGutter>;
    annotation: Annotation;
    selectedAnnotation: Maybe<Annotation>;
    gutters: TableGutterMap;
    onGuttersChanged: (s: TableGutterMap) => void;
    isCellMode: boolean;
    onMouseUpHandler: () => void;
    scaledCells: Annotation[];
    onScaledCellsChanged: (s: Annotation[]) => void;
};

export const useGutterMove: UseGutterMoveHook = ({
    panoRef,
    annotation,
    selectedAnnotation,
    selectedGutter,
    gutters,
    onGuttersChanged,
    isCellMode,
    onMouseUpHandler,
    scaledCells,
    onScaledCellsChanged
}) => {
    const [xDeltaState, setXDeltaState] = useState<number>(0);
    const [yDeltaState, setYDeltaState] = useState<number>(0);

    const getNewPositionOrBorderIfExceeded = (
        startPos: number,
        delta: number,
        type: GutterType
    ): number => {
        if (delta === 0) return startPos;
        const newPos = startPos + delta;
        if (newPos < Math.max(0, selectedGutter!.maxGap.leftBoundary))
            return Math.max(0, selectedGutter!.maxGap.leftBoundary);
        const gap =
            (type === 'vertical' ? annotation.bound.width : annotation.bound.height) -
            selectedGutter!.draggableGutterWidth;
        return Math.min(newPos, Math.min(selectedGutter!.maxGap.rightBoundary, gap));
    };

    const handleMouseMove = (start: Point, end: Point, target: HTMLElement) => {
        if (isClickedNotOnGutter(target)) return false;
        const xDelta = selectedGutter!.type === 'vertical' ? end.x - start.x : 0;
        setXDeltaState(xDelta);
        const yDelta = selectedGutter!.type === 'horizontal' ? end.y - start.y : 0;
        setYDeltaState(yDelta);
        const newPosition: GutterPosition = {
            start: {
                x: getNewPositionOrBorderIfExceeded(
                    selectedGutter!.stablePosition.start.x,
                    xDelta,
                    selectedGutter!.type
                ),
                y: getNewPositionOrBorderIfExceeded(
                    selectedGutter!.stablePosition.start.y,
                    yDelta,
                    selectedGutter!.type
                )
            },
            end: {
                x: getNewPositionOrBorderIfExceeded(
                    selectedGutter!.stablePosition.end.x,
                    xDelta,
                    selectedGutter!.type
                ),
                y: getNewPositionOrBorderIfExceeded(
                    selectedGutter!.stablePosition.end.y,
                    yDelta,
                    selectedGutter!.type
                )
            }
        };
        const realXDelta =
            selectedGutter!.type === 'vertical'
                ? newPosition.start.x - selectedGutter!.stablePosition.start.x
                : 0;
        setXDeltaState(realXDelta);
        const realYDelta =
            selectedGutter!.type === 'horizontal'
                ? newPosition.start.y - selectedGutter!.stablePosition.start.y
                : 0;
        setYDeltaState(realYDelta);
        let gtrs = gutters;
        gtrs[selectedGutter!.id] = {
            ...(selectedGutter as TableGutter),
            stablePosition: newPosition
        };
        onGuttersChanged(gtrs);
    };

    const isClickedNotOnGutter = (target: HTMLElement): boolean => {
        return (
            isCellMode ||
            !possiblyClickedOnTableGutter(target) ||
            !selectedGutter ||
            !Object.values(selectedGutter).length ||
            !selectedAnnotation ||
            selectedAnnotation.id !== annotation.id
        );
    };

    const findNeighbourGutter = (
        selectedGutter: TableGutter,
        direction: 'prev' | 'next'
    ): Maybe<TableGutter> => {
        let closestGutter: Maybe<TableGutter> = undefined;
        const possibleGutter = gutters[selectedGutter.id + (direction === 'next' ? 1 : -1)];
        if (possibleGutter && possibleGutter.type === selectedGutter.type)
            closestGutter = possibleGutter;
        return closestGutter;
    };

    const getRelativeGutterIndex = (): number => {
        let idx = 0;
        let prevGutter = findNeighbourGutter(selectedGutter!, 'prev');
        while (prevGutter) {
            idx = idx + 1;
            prevGutter = findNeighbourGutter(prevGutter, 'prev');
        }
        return idx;
    };

    const recalculateGutterPartsAfterMouseUp = (
        gutter: TableGutter,
        idx: number,
        delta: number
    ): GutterPart[] => {
        let newParts: GutterPart[] = gutter.parts;
        if (newParts.length > 1) {
            newParts[idx].length += delta;
            newParts[idx + 1].length -= delta;
        }
        return newParts;
    };

    const recalculatedAffectedCells = () => {
        const delta: number = selectedGutter!.type === 'vertical' ? xDeltaState : yDeltaState;
        const selector: string = selectedGutter!.type === 'vertical' ? 'col' : 'row';
        const boundSelector: 'width' | 'height' =
            selectedGutter!.type === 'vertical' ? 'width' : 'height';
        const coordSelector: 'x' | 'y' = selectedGutter!.type === 'vertical' ? 'x' : 'y';
        const relativeIdx = getRelativeGutterIndex();
        const newCells: Annotation[] = [];
        for (let cell of scaledCells) {
            const newCell: Annotation = cell;
            if (
                cell.data[selector] +
                    (cell.data[`${selector}span`] ? cell.data[`${selector}span`] - 1 : 0) ===
                relativeIdx
            ) {
                newCell.bound[boundSelector] += delta;
            } else if (cell.data[selector] === relativeIdx + 1) {
                newCell.bound[boundSelector] -= delta;
                newCell.bound[coordSelector] += delta;
            }
            newCells.push(newCell);
        }
        onScaledCellsChanged(newCells);
    };

    const recalculateGutterGapsAndPartsAfterMouseUp = () => {
        const prevGutter = findNeighbourGutter(selectedGutter!, 'prev');
        const nextGutter = findNeighbourGutter(selectedGutter!, 'next');
        const delta: number = selectedGutter!.type === 'vertical' ? xDeltaState : yDeltaState;
        let gtrs = gutters;
        if (prevGutter) {
            prevGutter.maxGap.rightBoundary += delta;
            gtrs[selectedGutter!.id - 1] = prevGutter;
        }
        if (nextGutter) {
            nextGutter.maxGap.leftBoundary += delta;
            gtrs[selectedGutter!.id + 1] = nextGutter;
        }
        const relativeIdx = getRelativeGutterIndex();
        for (let gutter of Object.values(gtrs)) {
            if (gutter.type === selectedGutter!.type) continue;
            const newParts = recalculateGutterPartsAfterMouseUp(gutter, relativeIdx, delta);
            gtrs[gutter.id] = {
                ...gtrs[gutter.id],
                parts: newParts
            };
        }
        recalculatedAffectedCells();
        onGuttersChanged(gtrs);
    };

    useMouseEvents({
        ref: panoRef,
        onMouseDown(_, target: HTMLElement) {
            if (isClickedNotOnGutter(target)) return false;
        },
        onMouseMove: handleMouseMove,
        onMouseUp(_, __, target: HTMLElement) {
            if (isClickedNotOnGutter(target)) return false;

            recalculateGutterGapsAndPartsAfterMouseUp();
            onMouseUpHandler();
        }
    });
};
