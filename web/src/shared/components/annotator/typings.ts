import { Category, Link } from 'api/typings';
import React, { RefObject } from 'react';
import paper from 'paper';

export type AnnotationBoundType = 'box' | 'free-box' | 'table' | 'text' | 'table_cell' | 'polygon';

export type NumberBounds = {
    value: number;
    bounds: {
        min: number;
        max: number;
    };
};

export type PenToolParams = {
    stroke: NumberBounds;
};
export type BrushToolParams = {
    radius: NumberBounds;
};

export type EraserToolParams = BrushToolParams;

export type WandToolParams = {
    threshold: NumberBounds;
    deviation: NumberBounds;
};

export type PaperToolParamsType = 'slider' | 'number' | 'slider-number';

export type PaperToolParams = {
    type: PaperToolParamsType;
    values: PenToolParams | BrushToolParams | EraserToolParams | WandToolParams;
};

export type PaperTool = {
    tool: paper.Tool;
    path: paper.Path;
    cocoSegments: number[][];
    selection?: paper.Path;
    params: PaperToolParams;
};
export enum ToolNames {
    pen = 'pen',
    brush = 'brush',
    eraser = 'eraser',
    wand = 'wand',
    dextr = 'dextr',
    rectangle = 'rectangle',
    select = 'select'
}

export type AnnotationImageTool = Record<ToolNames, PaperTool | undefined>;

export type AnnotationLinksBoundType = 'Chain' | 'All to all';

export type AnnotationBoundMode = 'box' | 'link' | 'segmentation' | 'document';
export type AnnotationLabel = {
    annotationId?: string | number;
    label?: string;
    color?: string;
};
export type Annotation = {
    id: string | number;
    boundType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames;
    bound: Bound;
    pageSize?: { width: number; height: number };
    category?: number | string;
    categoryName?: string;
    color?: string;
    label?: string;
    style?: Pick<React.CSSProperties, 'border' | 'color'>;
    tokens?: PageToken[];
    links?: Link[];
    table?: AnnotationTable;
    data?: any; // TODO: need to define proper types for data
    tableCells?: Maybe<Annotation[]>;
    children?: (string | number)[];
    segments?: number[][];
    labels?: AnnotationLabel[];
    originalAnnotationId?: number;
    text?: string;
};

export type Bound = {
    x: number;
    y: number;
    width: number;
    height: number;
};

export type AnnotationRenderer = (props: {
    annotation: Annotation;
    scale: number;
    page: number;
}) => React.ReactNode;

export type EditableAnnotationRenderer = (
    props: { annotation: Annotation } & {
        cells: Maybe<Annotation[]>;
        isSelected: boolean;
        isHovered?: boolean;
        selectedAnnotationRef?: RefObject<HTMLDivElement>;
        onClick: React.MouseEventHandler<HTMLDivElement>;
        onDoubleClick: React.MouseEventHandler<HTMLDivElement>;
        onContextMenu: React.MouseEventHandler<HTMLDivElement>;
        onAnnotationContextMenu?: (
            event: React.MouseEvent<HTMLDivElement>,
            annotationId: string | number,
            labels?: AnnotationLabel[]
        ) => void;
        onCloseIconClick: React.MouseEventHandler<HTMLDivElement>;
        onAnnotationDelete?: (id: string | number) => void;
        onMouseEnter?: React.MouseEventHandler<HTMLDivElement>;
        onMouseLeave?: React.MouseEventHandler<HTMLDivElement>;
        scale?: number;
        panoRef?: RefObject<HTMLDivElement>;
        isCellMode?: boolean;
        editable: boolean;
        page?: number;
        categories: Maybe<Category[]>;
        tools: AnnotationImageTool;
        setTools: (t: AnnotationImageTool) => void;
        canvas: boolean;
    }
) => React.ReactNode;

export type PageToken = {
    id?: number;
    text: string;
    previous?: string;
    after?: string;
    style?: Pick<React.CSSProperties, 'background' | 'opacity'>;
} & Bound;

export type Rect = { right: number; left: number; bottom: number; top: number };

export type TokenStyle = Pick<React.CSSProperties, 'background' | 'opacity'>;

export type AnnotationsStyle = {
    [key in AnnotationBoundType]: Pick<React.CSSProperties, 'border'>;
};

export type Point = {
    x: number;
    y: number;
};

export type GutterPosition = {
    start: Point;
    end: Point;
};

export type GutterType = 'vertical' | 'horizontal';

export type GutterPart = {
    length: number;
    visibility: boolean;
};

export type TableCell = {
    bound: Bound;
};

export type Maybe<T> = T | undefined;

export type TableGutter = {
    stablePosition: GutterPosition;
    type: GutterType;
    draggableGutterWidth: number;
    visibleGutterWidth: number;
    maxGap: {
        leftBoundary: number;
        rightBoundary: number;
    };
    id: number;
    parts: GutterPart[];
};

export type TableProps = {
    gutters: TableGutter[];
};

export type TableAnnotationProps = {
    label?: string;
    color?: string;
    bound: Bound;
    isSelected?: boolean;
    isEditable?: boolean;
    annotationRef?: RefObject<HTMLDivElement>;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
    onDoubleClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    panoRef: RefObject<HTMLDivElement>;
    annotation: Annotation;
    scale: number;
    isCellMode: boolean;
    id: number | string;
    page: number;
    cells: Maybe<Annotation[]>;
    categories: Maybe<Category[]>;
};

export type TableGutterMap = {
    [key: number]: TableGutter;
};

export type GutterParams = {
    draggableGutterWidth: number;
    visibleGutterWidth: number;
};

export type TableApi = {
    cols: number[];
    rows: number[];
};

export type AnnotationTable = {
    cols: number[];
    rows: number[];
};
