import { useMemo } from 'react';
import { Point, PageToken, Annotation, Rect, AnnotationBoundType, ToolNames } from '../typings';
import { isIntersected } from '../utils/is-intersected';
import { tokenToRect, annotationToRect } from '../utils/to-rect-utils';
import { getRectFrom2Points } from '../utils/get-rect-from-2-points';
import { downScaleCoords } from '../utils/down-scale-coords';
import { getMultilineTextTokens } from '../utils/calculate-distance';
import { AnnotationLinksBoundType } from 'shared';

type SelectionTokensPropsType = {
    selectionCoords: Point[];
    tokens: PageToken[];
    scale: number;
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames;
};
type AnnotationsTokensPropsType = {
    tokens: PageToken[];
    annotations: Annotation[];
};
type TokensByResizingPropsType = {
    tokens: PageToken[];
    resizedBoxAnnotationCoords: Point[];
    scale: number;
};

export const useSelectionTokens = ({
    selectionCoords,
    tokens,
    scale,
    selectionType
}: SelectionTokensPropsType) => {
    return useMemo(() => {
        if (tokens && selectionCoords.length === 2) {
            const scaledCoords = downScaleCoords(selectionCoords, scale);
            if (selectionType === 'box') {
                const coordsRect = getRectFrom2Points(scaledCoords[0], scaledCoords[1]);
                return tokens.filter((token) => isIntersected(tokenToRect(token), coordsRect));
            }
            if (selectionType === 'text') {
                return getMultilineTextTokens(tokens, scaledCoords).map((token) => ({
                    ...token,
                    style: { background: 'transparent' }
                }));
            }
        }
        return [];
    }, [scale, tokens, selectionCoords]);
};

export const useAnnotationsTokens = ({ tokens, annotations }: AnnotationsTokensPropsType) => {
    return useMemo(() => {
        const tokenRects = tokens.reduce<Record<number, Rect>>((map, token) => {
            map[token.id as number] = tokenToRect(token);
            return map;
        }, {});

        return annotations.flatMap((ann) => {
            if (ann.boundType === 'text') {
                if (ann.tokens)
                    return ann.tokens.map((token) => ({
                        ...token,
                        style: { background: 'transparent' }
                    })) as PageToken[];
                return [];
            }

            const annRect = annotationToRect(ann);
            return tokens.reduce((tokens: PageToken[], token) => {
                if (isIntersected(tokenRects[Number(token.id)], annRect)) {
                    token.style = { background: ann.color };

                    tokens.push(token);
                }
                return tokens;
            }, []);
        });
    }, [tokens, annotations]);
};

export const useTokensByResizing = ({
    tokens,
    resizedBoxAnnotationCoords,
    scale
}: TokensByResizingPropsType) => {
    return useMemo(() => {
        if (tokens && resizedBoxAnnotationCoords.length === 2) {
            const scaledCoords = downScaleCoords(resizedBoxAnnotationCoords, scale);
            const resizedCoordsRect = getRectFrom2Points(scaledCoords[0], scaledCoords[1]);
            return tokens.filter((token) => isIntersected(tokenToRect(token), resizedCoordsRect));
        }
        return [];
    }, [scale, tokens, resizedBoxAnnotationCoords]);
};
