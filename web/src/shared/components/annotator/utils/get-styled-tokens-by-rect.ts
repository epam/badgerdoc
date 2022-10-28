import { CSSProperties } from 'react';
import { PageToken, Rect } from '../typings';
import { isIntersected } from './is-intersected';
import { tokenToRect } from './to-rect-utils';

export const getStyledTokensByRect = (
    tokens: PageToken[],
    rect: Rect,
    style?: Pick<CSSProperties, 'background' | 'opacity'>
): PageToken[] => {
    const resultTokens: PageToken[] = [];

    tokens.forEach((token) => {
        if (isIntersected(tokenToRect(token), rect)) {
            resultTokens.push(token);
            token.style = style;
        }
    });

    return resultTokens;
};
