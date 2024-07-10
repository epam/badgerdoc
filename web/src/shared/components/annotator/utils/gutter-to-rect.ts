import { Bound, Rect, TableGutter } from '../typings';

export const gutterToRect = (annotationBound: Bound, gutter: TableGutter, scale: number): Rect => {
    const { start, end } = gutter.stablePosition;
    const type = gutter.type;
    return {
        top:
            (annotationBound.y +
                start.y -
                (type === 'horizontal' ? gutter.draggableGutterWidth : 0)) /
            scale,
        bottom:
            (annotationBound.y +
                end.y +
                (type === 'horizontal' ? gutter.draggableGutterWidth : 0)) /
            scale,
        right:
            (annotationBound.x + end.x) / scale + (type === 'vertical' ? gutter.draggableGutterWidth / 2 : 0),
        left:
            (annotationBound.x + start.x) / scale  - (type === 'vertical' ? gutter.draggableGutterWidth / 2 : 0)
    };
};
