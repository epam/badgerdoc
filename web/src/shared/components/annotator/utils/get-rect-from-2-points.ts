import { Point, Rect } from '../typings';

export const getRectFrom2Points = (start: Point, end: Point): Rect => {
    const left = Math.min(start.x, end.x);
    const right = Math.max(start.x, end.x);
    const top = Math.min(start.y, end.y);
    const bottom = Math.max(start.y, end.y);

    return { left, right, top, bottom };
};
