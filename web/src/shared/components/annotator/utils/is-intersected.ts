import { Point, Rect } from '../typings';

export const isIntersected = (r1: Rect, r2: Rect) => {
    return !(r2.left > r1.right || r2.right < r1.left || r2.top > r1.bottom || r2.bottom < r1.top);
};

export const isR2InsideR1 = (r1: Rect, r2: Rect) => {
    return r2.left >= r1.left && r2.right <= r1.right && r2.top >= r1.top && r2.bottom <= r1.bottom;
};

export const isPointInsideRect = (rect: Rect, coords: Point) => {
    return (
        rect.left <= coords.x &&
        rect.right >= coords.x &&
        rect.top <= coords.y &&
        rect.bottom >= coords.y
    );
};
