import { Annotation, PageToken } from '../typings';
import { getStyledTokensByRect } from './get-styled-tokens-by-rect';
import { annotationToRect } from './to-rect-utils';

export const getSelectedTokensForAnnotations = (
    annotations: Annotation[],
    tokens: PageToken[]
): PageToken[] => {
    const tokenSet = new Set<PageToken>();

    annotations.forEach((annotation) => {
        const annotationRect = annotationToRect(annotation);
        const style = annotation && {
            background: annotation.color,
            opacity: 0.2
        };

        getStyledTokensByRect(tokens, annotationRect, style).forEach((token) =>
            tokenSet.add(token)
        );
    });

    return Array.from(tokenSet);
};
