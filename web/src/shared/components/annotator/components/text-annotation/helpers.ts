import { AnnotationLabel, Bound, PageToken } from '../../typings';
import React from 'react';

const MIN_GAP_INTER_LINES_TO_SHOW_LABEL = 10;
const MIN_GAP_BETWEEN_START_END_LABELS = 250;

export type TextAnnotationProps = {
    label?: React.ReactNode;
    labels?: AnnotationLabel[];
    color?: string;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    onAnnotationContextMenu?: (
        event: React.MouseEvent<HTMLDivElement>,
        annotationId: string | number,
        labels?: AnnotationLabel[]
    ) => void;

    onAnnotationDelete?: (id: string | number) => void;
    onDoubleClick?: React.MouseEventHandler<HTMLDivElement>;
    onMouseEnter?: React.MouseEventHandler<HTMLDivElement>;
    onMouseLeave?: React.MouseEventHandler<HTMLDivElement>;

    tokens: PageToken[];
    scale: number;
    isEditable?: boolean;
    isSelected?: boolean;
    id?: string | number;
    page: number;
    isHovered?: boolean;
    taskHasTaxonomies?: boolean;
};

type LabelPosition = 'start' | 'end' | 'middle' | 'both' | 'no_label';

export type TextAnnotationLabelProps = {
    color: string;
    labelPosition: LabelPosition;
    label?: React.ReactNode;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    isEditable?: boolean;
    isSelected?: boolean;
    isHovered?: boolean;
    taskHasTaxonomies?: boolean;
};

type TextAnnBoundParams = {
    /**
     * Where is the label positioned - on the left, on the right, in the middle, both sides or nowhere
     */
    labelPosition: LabelPosition;
    /**
     * Is this bound also an annotation start/end/single-liner ?
     */
    boundPositionInAnnotation: 'textStart' | 'textEnd' | 'both' | 'other';
};

export type TextAnnBound = {
    /**
     * Dimensions for render purposes
     */
    bound: Bound;
    /**
     * Meta params (labelPosition, textboundPositionInAnnotation)
     */
    params: TextAnnBoundParams;
};

export const isBoundValid = (bound: Bound): boolean =>
    'x' in bound && 'y' in bound && 'width' in bound && 'height' in bound;

const canFitLabelBetweenLines = (prevBound: Bound, curBound: Bound): boolean => {
    const interlineGap = curBound.y - curBound.height - prevBound.y;
    return interlineGap > MIN_GAP_INTER_LINES_TO_SHOW_LABEL;
};

const isLineWideEnough = (curBound: Bound, scale: number): boolean => {
    return curBound.width * scale > MIN_GAP_BETWEEN_START_END_LABELS;
};

const getLabelPosition = (prevBound: Bound, curBound: Bound, scale: number): LabelPosition => {
    if (!isBoundValid(prevBound)) {
        return 'end';
    }
    const startLabel: boolean = canFitLabelBetweenLines(prevBound, curBound);
    const endLabel: boolean =
        canFitLabelBetweenLines(prevBound, curBound) && isLineWideEnough(curBound, scale);
    if (startLabel && endLabel) return 'both';
    if (startLabel) return 'start';
    if (endLabel) return 'end';
    return 'no_label';
};

export const updateCurrentTextAnnBound = (curBound: Bound, token: PageToken): Bound => {
    if (!isBoundValid(curBound)) return token;
    return {
        x: curBound.x,
        y: Math.max(token.y, curBound.y),
        height: Math.max(token.height, curBound.height),
        width: token.x + token.width - curBound.x
    };
};

export const isTokenOnNewLine = (token: PageToken, curBound: Bound): boolean => {
    return isBoundValid(curBound) && token.y > curBound.y + token.height;
};

const createRegularTextAnnBoundParams = (
    curBound: Bound,
    prevBound: Bound,
    boundsCreated: number,
    scale: number
): TextAnnBoundParams => {
    const labelPosition = getLabelPosition(prevBound, curBound, scale);
    const boundPositionInAnnotation = boundsCreated === 0 ? 'textStart' : 'other';
    return { labelPosition, boundPositionInAnnotation };
};

const createFinalTextAnnBoundParams = (
    curBound: Bound,
    prevBound: Bound,
    boundsCreated: number
): TextAnnBoundParams => {
    const startLabel = boundsCreated > 0 && canFitLabelBetweenLines(prevBound, curBound);
    const middleLabel = boundsCreated === 0;
    const labelPosition = startLabel ? 'start' : middleLabel ? 'middle' : 'no_label';
    const boundPositionInAnnotation = boundsCreated === 0 ? 'both' : 'textEnd';
    return { labelPosition, boundPositionInAnnotation };
};

export const createTextAnnBound = (
    curBound: Bound,
    prevBound: Bound,
    boundsCreated: number,
    mode: 'regular' | 'final',
    scale: number
): TextAnnBound => {
    const creatorFn =
        mode === 'regular' ? createRegularTextAnnBoundParams : createFinalTextAnnBoundParams;
    const boundParams = creatorFn(curBound, prevBound, boundsCreated, scale);
    return {
        bound: curBound,
        params: boundParams
    };
};

export const getBorders = (bound: TextAnnBound, color: string): string => {
    if (bound.params.boundPositionInAnnotation === 'both')
        return `2px 0px 0px ${color}, -2px 0px 0px ${color}`;
    if (bound.params.boundPositionInAnnotation === 'textStart') return `-2px 0px 0px ${color}`;
    if (bound.params.boundPositionInAnnotation === 'textEnd') return `2px 0px 0px ${color}`;
    return 'none';
};

export const createBoundsFromTokens = (tokens: PageToken[], scale: number): TextAnnBound[] => {
    const textAnnBounds: TextAnnBound[] = [];
    let curBound: Bound = {} as Bound;
    let prevBound: Bound = {} as Bound;
    let boundsCreated = 0;
    if (!tokens) return [];
    for (let token of tokens) {
        if (isTokenOnNewLine(token, curBound)) {
            const newTextAnnBound: TextAnnBound = createTextAnnBound(
                curBound,
                prevBound,
                boundsCreated,
                'regular',
                scale
            );
            textAnnBounds.push(newTextAnnBound);
            prevBound = curBound;
            curBound = {} as Bound;
            boundsCreated++;
        }
        curBound = updateCurrentTextAnnBound(curBound, token);
    }
    const newTextAnnBound: TextAnnBound = createTextAnnBound(
        curBound,
        prevBound,
        boundsCreated,
        'final',
        scale
    );
    textAnnBounds.push(newTextAnnBound);
    return textAnnBounds;
};
