import { PageToken, Point } from '../typings';
import { tokenToRect } from './to-rect-utils';
import { isPointInsideRect } from './is-intersected';

type DistanceMode = 'l1' | 'l2' | 'linf';

const distanceBetweenPoints = (pointA: Point, pointB: Point, mode: DistanceMode = 'l2'): number => {
    switch (mode) {
        case 'l1':
            return Math.abs(pointA.x - pointB.x) + Math.abs(pointA.y - pointB.y);
        case 'l2':
            return Math.sqrt(
                (pointA.x - pointB.x) * (pointA.x - pointB.x) +
                    (pointA.y - pointB.y) * (pointA.y - pointB.y)
            );
        case 'linf':
            return Math.max(Math.abs(pointA.x - pointB.x), Math.abs(pointA.y - pointB.y));
    }
};

const getDistanceToToken = (token: PageToken, point: Point): number => {
    //TODO: We obviously need to calculate distance fairly (get point's projection on every arbitrary surface),
    //but for now we can use simple 'distance to token's center'. The reasons are:
    //1. Simplicity (we can think about this as an MVP)
    //2. Tokens are usually rather small, so this approach wouldn't be very inaccurate anyway
    const tokenRect = tokenToRect(token);
    const tokenRectCenter: Point = {
        x: (tokenRect.left + tokenRect.right) / 2,
        y: (tokenRect.top + tokenRect.bottom) / 2
    };
    return distanceBetweenPoints(tokenRectCenter, point, 'l2');
};

export const getNearestTokenToPoint = (tokens: PageToken[], point: Point): PageToken => {
    let nearestToken: PageToken = {} as PageToken;
    let distance = Number.MAX_SAFE_INTEGER;
    for (let token of tokens) {
        if (isPointInsideRect(tokenToRect(token), point)) return token;
        const curDist = getDistanceToToken(token, point);
        if (curDist < distance) {
            distance = curDist;
            nearestToken = token;
        }
    }
    return nearestToken;
};

export const getMultilineTextTokens = (tokens: PageToken[], coords: Point[]): PageToken[] => {
    const firstToken = getNearestTokenToPoint(tokens, coords[0]);
    const lastToken = getNearestTokenToPoint(tokens, coords[1]);
    if (!firstToken.id || !lastToken.id) return [];
    const firstId = Math.min(firstToken.id, lastToken.id);
    const lastId = Math.max(firstToken.id, lastToken.id);
    return tokens.slice(firstId, lastId + 1);
};
