// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import { RefObject } from 'react';
import { Annotation, Point, Bound, TableGutter, GutterType, TableGutterMap, Maybe } from '..';
import { useMouseEvents } from './use-mouse-events';
import { isPointInsideRect } from '../utils/is-intersected';
import { annotationToRect } from '../utils/to-rect-utils';

type UseCellSelectionHook = (params: CellSelectionParams) => void;

type CellSelectionParams = {
    panoRef: RefObject<HTMLDivElement>;
    selectedAnnotation: Maybe<Annotation>;
    annotation: Annotation;
    gutters: TableGutterMap;
    onSelectedBoundsChanged: (s: Bound) => void;
    isCellMode: boolean;
    scaledCells: Annotation[];
    onSelectedCellsChanged: (s: Annotation[]) => void;
};

type NearestGutters = {
    leftGutter: Maybe<TableGutter>;
    topGutter: Maybe<TableGutter>;
    rightGutter: Maybe<TableGutter>;
    bottomGutter: Maybe<TableGutter>;
};

export const useCellSelection: UseCellSelectionHook = ({
    panoRef,
    selectedAnnotation,
    annotation,
    gutters,
    onSelectedBoundsChanged,
    isCellMode,
    scaledCells,
    onSelectedCellsChanged
}) => {
    const isClickOnVisiblePart = (pointOnGutter: number, gutter: TableGutter): boolean => {
        let sum = 0;
        for (let part of gutter.parts) {
            sum += part.length;
            if (pointOnGutter <= sum) return part.visibility;
        }
        return true; //If we move mouse out of table
    };

    const findNearestGutters = (point: Point): NearestGutters => {
        /* Find two nearest gutter parts, they are minimal negative and minimal positive distance and be visible */
        let closestLeft: Maybe<TableGutter> = undefined;
        let closestRight: Maybe<TableGutter> = undefined;
        let closestTop: Maybe<TableGutter> = undefined;
        let closestBottom: Maybe<TableGutter> = undefined;
        let vDistPositive: number = Number.MAX_SAFE_INTEGER;
        let vDistNegative: number = Number.MIN_SAFE_INTEGER;
        let hDistPositive: number = Number.MAX_SAFE_INTEGER;
        let hDistNegative: number = Number.MIN_SAFE_INTEGER;
        for (let gutter of Object.values(gutters as TableGutterMap)) {
            const gutterKey = gutter.type === 'vertical' ? 'x' : 'y';
            const gutterPos = gutter.stablePosition.start[gutterKey];
            const distPointPos = point[gutterKey] - annotation.bound[gutterKey];
            const visiblePointPos =
                gutter.type === 'horizontal'
                    ? point.x - annotation.bound.x
                    : point.y - annotation.bound.y;
            const dist = gutterPos - distPointPos;
            if (isClickOnVisiblePart(visiblePointPos, gutter)) {
                if (gutter.type === 'vertical') {
                    if (dist > 0 && dist < vDistPositive) {
                        vDistPositive = dist;
                        closestRight = gutter;
                    }
                    if (dist < 0 && dist > vDistNegative) {
                        vDistNegative = dist;
                        closestLeft = gutter;
                    }
                }
                if (gutter.type === 'horizontal') {
                    if (dist > 0 && dist < hDistPositive) {
                        hDistPositive = dist;
                        closestBottom = gutter;
                    }
                    if (dist < 0 && dist > hDistNegative) {
                        hDistNegative = dist;
                        closestTop = gutter;
                    }
                }
            }
        }
        return {
            leftGutter: closestLeft,
            topGutter: closestTop,
            rightGutter: closestRight,
            bottomGutter: closestBottom
        };
    };

    const findExtremalGutters = (start: NearestGutters, end: NearestGutters): NearestGutters => {
        let leftGutter: Maybe<TableGutter> = undefined;
        let topGutter: Maybe<TableGutter> = undefined;
        let rightGutter: Maybe<TableGutter> = undefined;
        let bottomGutter: Maybe<TableGutter> = undefined;
        if (start.leftGutter && end.leftGutter) {
            if (start.leftGutter.stablePosition.start.x < end.leftGutter.stablePosition.start.x)
                leftGutter = start.leftGutter;
            else leftGutter = end.leftGutter;
        }
        if (start.rightGutter && end.rightGutter) {
            if (start.rightGutter.stablePosition.start.x > end.rightGutter.stablePosition.start.x)
                rightGutter = start.rightGutter;
            else rightGutter = end.rightGutter;
        }
        if (start.topGutter && end.topGutter) {
            if (start.topGutter.stablePosition.start.y < end.topGutter.stablePosition.start.y)
                topGutter = start.topGutter;
            else topGutter = end.topGutter;
        }
        if (start.bottomGutter && end.bottomGutter) {
            if (start.bottomGutter.stablePosition.start.y > end.bottomGutter.stablePosition.start.y)
                bottomGutter = start.bottomGutter;
            else bottomGutter = end.bottomGutter;
        }
        return {
            leftGutter,
            topGutter,
            rightGutter,
            bottomGutter
        };
    };

    const handleMouseMove = (start: Point, end: Point, target: HTMLElement) => {
        if (isNotCellSelectionMode(target)) return false;
        const startCell: Maybe<Annotation> = scaledCells.find((el) =>
            isPointInsideRect(annotationToRect(el), start)
        );
        const endCell: Maybe<Annotation> = scaledCells.find((el) =>
            isPointInsideRect(annotationToRect(el), end)
        );
        if (!startCell || !endCell) return;
        const affectedCells = scaledCells
            .filter(
                (el) =>
                    el.data.col + (el.data.colspan ? el.data.colspan - 1 : 0) >=
                        Math.min(startCell.data.col, endCell.data.col) &&
                    el.data.col <=
                        Math.max(
                            startCell.data.col +
                                (startCell.data.colspan ? startCell.data.colspan - 1 : 0),
                            endCell.data.col + (endCell.data.colspan ? endCell.data.colspan - 1 : 0)
                        ) &&
                    el.data.row + (el.data.rowspan ? el.data.rowspan - 1 : 0) >=
                        Math.min(startCell.data.row, endCell.data.row) &&
                    el.data.row <=
                        Math.max(
                            startCell.data.row +
                                (startCell.data.rowspan ? startCell.data.rowspan - 1 : 0),
                            endCell.data.row + (endCell.data.rowspan ? endCell.data.rowspan - 1 : 0)
                        )
            )
            .sort((a, b) => parseInt(a.id as string) - parseInt(b.id as string));
        onSelectedCellsChanged(affectedCells);
        const selectedGuttersStart = findNearestGutters(start);
        const selectedGuttersEnd = findNearestGutters(end);
        const selectionGutters: NearestGutters = findExtremalGutters(
            selectedGuttersStart,
            selectedGuttersEnd
        );
        const bound: Bound = getBoundingParams(selectionGutters);
        onSelectedBoundsChanged(bound);
    };

    const getDimensionalParams = (
        startGutter: Maybe<TableGutter>,
        endGutter: Maybe<TableGutter>,
        type: GutterType
    ): { startPoint: number; endPoint: number } => {
        const tableBorderThickness = 4; // TODO: 4 is purely heuristical constant === table border thickness
        const gutterKey = type === 'horizontal' ? 'x' : 'y';
        const annotationKey = type === 'horizontal' ? 'width' : 'height';
        let startPoint = 0;
        if (startGutter) {
            const offset =
                startGutter.draggableGutterWidth / 2 - startGutter.visibleGutterWidth * 2;
            startPoint = startGutter.stablePosition.start[gutterKey] + offset;
        }
        let endPoint = annotation.bound[annotationKey] - startPoint - tableBorderThickness;
        if (endGutter) {
            const offset = endGutter.draggableGutterWidth / 2 - endGutter.visibleGutterWidth * 3;
            endPoint = endGutter.stablePosition.start[gutterKey] - startPoint + offset;
        }
        return {
            startPoint,
            endPoint
        };
    };

    const getBoundingParams = (selectionGutters: NearestGutters): Bound => {
        const horizontalParams = getDimensionalParams(
            selectionGutters.leftGutter,
            selectionGutters.rightGutter,
            'horizontal'
        );
        const verticalParams = getDimensionalParams(
            selectionGutters.topGutter,
            selectionGutters.bottomGutter,
            'vertical'
        );
        return {
            x: horizontalParams.startPoint,
            y: verticalParams.startPoint,
            height: verticalParams.endPoint,
            width: horizontalParams.endPoint
        };
    };

    // todo: consider removal target param
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const isNotCellSelectionMode = (target: HTMLElement): boolean => {
        return !isCellMode || !selectedAnnotation || selectedAnnotation.id !== annotation.id;
    };

    useMouseEvents({
        ref: panoRef,
        onMouseDown(clickPoint, target: HTMLElement) {
            if (isNotCellSelectionMode(target)) return false;
            onSelectedBoundsChanged({} as Bound);
            onSelectedCellsChanged([]);
        },
        onMouseMove: handleMouseMove,
        onMouseUp(_, __, target: HTMLElement) {
            if (isNotCellSelectionMode(target)) return false;
        }
    });
};
