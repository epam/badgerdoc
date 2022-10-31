import noop from 'lodash/noop';
import React, { RefObject, useEffect } from 'react';
import { Annotation, AnnotationImageTool, Bound } from '../../typings';
import paper from 'paper';
import { removeAllSelections } from '../image-tools/utils';

type ImageAnnotationProps = {
    annotation: Annotation;
    label?: React.ReactNode;
    color?: string;
    bound: Bound;
    isSelected?: boolean;
    isEditable?: boolean;
    isHovered?: boolean;
    annotationRef?: RefObject<HTMLDivElement>;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
    onDoubleClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    id: number | string;
    page: number;
    boundType: string;
    onMouseEnter?: React.MouseEventHandler<HTMLDivElement>;
    onMouseLeave?: React.MouseEventHandler<HTMLDivElement>;
    segments: number[][];
    tools: AnnotationImageTool;
    setTools: (t: AnnotationImageTool) => void;
    canvas: boolean;
    scale: number;
};

export const ImageAnnotation = ({
    annotation,
    label = '',
    color = 'black',
    bound,
    isSelected,
    isEditable,
    isHovered,
    annotationRef,
    onClick = noop,
    onDoubleClick = noop,
    onContextMenu = noop,
    onCloseIconClick = noop,
    id,
    page,
    boundType,
    onMouseEnter = noop,
    onMouseLeave = noop,
    segments,
    tools,
    setTools,
    canvas,
    scale
}: ImageAnnotationProps) => {
    useEffect(() => {
        if (segments.length > 0 && canvas) {
            removeAllSelections();
            const toDelete = [];
            for (let child of paper.project.activeLayer.children) {
                if (
                    (child.data &&
                        child.data.annotationId &&
                        child.data.annotationId === annotation.id) ||
                    child.data.isBBox ||
                    child.data.isBrushSelection ||
                    child.data.isEraserSelection
                )
                    toDelete.push(child);
            }
            for (let d of toDelete) {
                d.remove();
            }
            const paperJSChildren = new paper.CompoundPath({
                children: [],
                closed: true,
                data: {
                    annotationId: annotation.id as string
                },
                fillColor: new paper.Color(color),
                strokeColor: new paper.Color(color)
            });
            paperJSChildren.fillColor!.alpha = 0.2;
            for (let segment of segments) {
                const copy = [...segment];
                const sgmts = [],
                    size = 2;
                while (copy.length > 0)
                    sgmts.push(new paper.Point(copy.splice(0, size).map((el) => (el *= scale))));
                const newChild = paper.PathItem.create(sgmts);
                newChild.simplify(1.5);
                newChild.data = {
                    annotationId: annotation.id as string
                };
                newChild.fillColor = new paper.Color(color);
                newChild.fillColor.alpha = 0.2;
                newChild.closed = true;
                paperJSChildren.addChild(newChild);
                /* TODO: A way to select only annotation that is drawn right now, not from backend?*/
            }
        }
    }, [segments, canvas]);
    return <></>;
};
