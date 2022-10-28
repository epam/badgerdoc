import { useCallback } from 'react';
import {
    Point,
    AnnotationBoundType,
    PageToken,
    Annotation,
    Bound,
    PaperTool,
    AnnotationImageToolType
} from '..';
import { getRectFrom2Points } from '../utils/get-rect-from-2-points';
import { isIntersected } from '../utils/is-intersected';
import { rectToBound } from '../utils/rect-to-bound';
import { tokenToRect } from '../utils/to-rect-utils';
import { getTokensBound } from '../utils/get-tokens-bound';
import { getMultilineTextTokens } from '../utils/calculate-distance';
import { AnnotationLinksBoundType } from 'shared';

const submitFreeBoxAnnotation = (
    coords: Point[],
    cb: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
) => {
    const selectionRect = getRectFrom2Points(coords[0], coords[1]);

    const ann = {
        boundType: 'free-box' as AnnotationBoundType,
        bound: rectToBound(selectionRect)
    };

    cb(ann);
};

const submitPolygonAnnotation = (
    tool: PaperTool,
    cb: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
) => {
    const bound: Bound = {
        x: tool.path.bounds.x,
        y: tool.path.bounds.y,
        width: tool.path.bounds.width,
        height: tool.path.bounds.height
    };
    const ann = {
        boundType: 'polygon' as AnnotationBoundType,
        bound: bound,
        segments: tool.cocoSegments
    };

    cb(ann);
};

const submitTableAnnotation = (
    coords: Point[],
    cb: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
) => {
    const selectionRect = getRectFrom2Points(coords[0], coords[1]);

    const ann = {
        boundType: 'table' as AnnotationBoundType,
        bound: rectToBound(selectionRect),
        /* No need to add api-related stuff just yet */
        table: {
            cols: [],
            rows: []
        },
        children: [],
        tableCells: []
    };
    cb(ann);
};

const submitBoxAnnotation = (
    coords: Point[],
    tokens: PageToken[],
    cb: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
) => {
    const selectionRect = getRectFrom2Points(coords[0], coords[1]);

    const selected = tokens.filter((t) => isIntersected(tokenToRect(t), selectionRect));

    if (!selected || !selected.length) return;

    const ann = {
        boundType: 'box' as AnnotationBoundType,
        bound: getTokensBound(selected)
    };

    cb(ann);
};

const submitTextAnnotation = (
    coords: Point[],
    tokens: PageToken[],
    cb: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
) => {
    const selected = getMultilineTextTokens(tokens, coords);

    if (!selected || !selected.length) return;

    const ann = {
        boundType: 'text' as AnnotationBoundType,
        bound: {} as Bound,
        tokens: selected
    };

    cb(ann);
};

export const useSubmitAnnotation = (
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType,
    tokens: PageToken[],
    onBoundCreated: (ann: Pick<Annotation, 'bound' | 'boundType'>) => void
): ((p: Point[] | PaperTool) => void) => {
    const polygonSubmit = useCallback(
        (p: PaperTool | Point[]): void => submitPolygonAnnotation(p as PaperTool, onBoundCreated),
        [selectionType, onBoundCreated]
    );
    const defaultSubmit = useCallback(
        (coords: PaperTool | Point[]) => submitFreeBoxAnnotation(coords as Point[], onBoundCreated),
        [selectionType, onBoundCreated]
    );

    const tableSubmit = useCallback(
        (coords: PaperTool | Point[]) => submitTableAnnotation(coords as Point[], onBoundCreated),
        [selectionType, onBoundCreated]
    );

    const boxSubmit = useCallback(
        (coords: PaperTool | Point[]) =>
            submitBoxAnnotation(coords as Point[], tokens, onBoundCreated),
        [selectionType, onBoundCreated, tokens, tokens.length]
    );

    const textSubmit = useCallback(
        (coords: PaperTool | Point[]) =>
            submitTextAnnotation(coords as Point[], tokens, onBoundCreated),
        [selectionType, onBoundCreated, tokens, tokens.length]
    );

    switch (selectionType) {
        case 'free-box':
            return defaultSubmit;
        case 'box':
            return boxSubmit;
        case 'text':
            return textSubmit;
        case 'table':
            return tableSubmit;
        case 'polygon':
            return polygonSubmit;
        default:
            return defaultSubmit;
    }
};
