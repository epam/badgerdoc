import React from 'react';
import { Point } from 'shared';
import { Category, Link } from 'api/typings';

export type LinkAnnotationProps = {
    pointStart: Point;
    pointFinish: Point;
    category: Category;
    linkType: string;
    onDeleteLink: () => void;
    onLinkSelect: () => void;
    reversed: boolean;
};

export const getAngleFromPoints = (lower: Point, higher: Point, add_rotation: number = 0) => {
    return add_rotation + Math.atan2(higher.y - lower.y, higher.x - lower.x);
};

export const getVectorLength = (point1: Point, point2: Point) => {
    return Math.sqrt((point1.y - point2.y) ** 2 + (point1.x - point2.x) ** 2);
};

export const getStyledLinkByBounds = (start: Point, finish: Point) => {
    let vectorLength, angle;

    vectorLength = getVectorLength(start, finish);
    angle = getAngleFromPoints(start, finish);
    return {
        transform: `rotate(${angle}rad) translateX(1px)`,
        width: `${vectorLength}px`,
        left: `${start.x}px`,
        top: `${start.y}px`
    };
};
