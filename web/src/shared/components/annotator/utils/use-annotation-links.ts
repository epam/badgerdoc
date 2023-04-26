import { Category } from 'api/typings';
import { useEffect, useRef } from 'react';
import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType
} from 'shared';

export type AnnotationLink = {
    prevSelected: Annotation;
    linkedWith: Annotation;
};

export const useAnnotationsLinks = (
    selectedAnn: Annotation | undefined,
    category: Category | undefined,
    current_page: number | undefined,
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType,
    allAnnotations: Record<number, Annotation[]>,
    onAnnotationEdited: (
        prevPage: number,
        links: Pick<Annotation, 'links'>,
        annId: number | string
    ) => void,
    setSelectedCategory: (category?: Category) => void
) => {
    const prevPage = useRef<number>();
    const prevSelectedAnnotation = useRef<Annotation>();

    useEffect(() => {
        if (category?.type !== 'link') {
            prevPage.current = undefined;
            prevSelectedAnnotation.current = undefined;
            return;
        }

        if (
            category &&
            selectedAnn &&
            current_page &&
            prevPage.current &&
            prevSelectedAnnotation.current &&
            prevSelectedAnnotation.current.id !== selectedAnn.id
        ) {
            const links = prevSelectedAnnotation.current.links
                ? [...prevSelectedAnnotation.current.links]
                : [];

            links.push({
                to: selectedAnn.id,
                category_id: category.id,
                page_num: selectedAnn.pageNum || current_page,
                type:
                    selectionType == AnnotationLinksBoundType.chain
                        ? 'directional'
                        : 'omnidirectional'
            });

            onAnnotationEdited(prevPage.current, { links }, prevSelectedAnnotation.current.id);
            setSelectedCategory(undefined);
            prevPage.current = undefined;
            prevSelectedAnnotation.current = undefined;
            return;
        }

        prevPage.current = selectedAnn?.pageNum;
        prevSelectedAnnotation.current = selectedAnn;
    }, [selectedAnn]);

    return allAnnotations;
};

export const getAnnotationElementId = (pageNum: number, elmId: string | number): string => {
    return `box-${pageNum}-${elmId}`;
};
