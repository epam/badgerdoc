import { Rect, Bound } from '../typings';

export const rectToBound = (rect: Rect): Bound => {
    return {
        x: rect.left,
        y: rect.top,
        width: rect.right - rect.left,
        height: rect.bottom - rect.top
    };
};

export const boundToRect = (bound: Bound): Rect => {
    return {
        left: bound.x,
        top: bound.y,
        right: bound.x + bound.width,
        bottom: bound.y + bound.height
    };
};
