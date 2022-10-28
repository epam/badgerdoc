import { PageInfoObjs } from 'api/typings';
import { Bound } from 'shared/components/annotator/typings';

export const boundToBBox = (bound: Bound): PageInfoObjs['bbox'] => {
    return [bound.x, bound.y, bound.x + bound.width, bound.y + bound.height];
};
