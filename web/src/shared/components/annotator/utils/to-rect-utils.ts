import { PageToken, Annotation, Rect } from '../typings';

export const tokenToRect = (t: PageToken): Rect => {
    return {
        left: t.x,
        right: t.x + t.width,
        top: t.y,
        bottom: t.y + t.height
    };
};

export const annotationToRect = (annotation: Annotation): Rect => {
    const { x, y, width, height } = annotation.bound;

    return {
        left: x,
        right: x + width,
        top: y,
        bottom: y + height
    };
};
