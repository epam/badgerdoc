import { Point, Rect } from '../typings';

export const get2PointsFromRect = (rect: Rect): [start: Point, end: Point] => {
    const p1 = {
        x: rect.left,
        y: rect.top
    };

    const p2 = {
        x: rect.right,
        y: rect.bottom
    };

    return [p1, p2];
};
