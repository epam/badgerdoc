import React from 'react';
import { BoxAnnotation } from '../../components/box-annotation';
import { AnnotationRenderer, PageToken } from '../../typings';
import { TextAnnotation } from '../../components/text-annotation';

export const defaultAnnotationRenderer: AnnotationRenderer = ({ annotation, scale, page }) => {
    if (annotation.boundType === 'text')
        return (
            <TextAnnotation
                key={annotation.id}
                tokens={annotation.tokens as PageToken[]}
                scale={scale}
                id={annotation.id}
                page={page}
            />
        );
    return <BoxAnnotation key={annotation.id} {...annotation} page={page} />;
};
