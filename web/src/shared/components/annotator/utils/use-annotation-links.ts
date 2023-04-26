import { Category } from 'api/typings';
import { useEffect, useState } from 'react';
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
    const [prevPage, setPrevPage] = useState<number>();
    const [prevSelected, setPrevSelected] = useState<Annotation>();

    useEffect(() => {
        if (category?.type !== 'link') {
            setPrevSelected(undefined);
            setPrevPage(undefined);
            return;
        }

        if (
            prevSelected &&
            selectedAnn &&
            category &&
            current_page &&
            prevPage &&
            prevSelected.id !== selectedAnn.id
        ) {
            const links = prevSelected.links ? [...prevSelected.links] : [];

            links.push({
                to: selectedAnn.id,
                page_num: current_page,
                category_id: category.id,
                type:
                    selectionType == AnnotationLinksBoundType.chain
                        ? 'directional'
                        : 'omnidirectional'
            });

            onAnnotationEdited(prevPage, { links }, prevSelected.id);
            setSelectedCategory(undefined);
            return;
        }

        setPrevSelected(selectedAnn);
        setPrevPage(current_page);
    }, [selectedAnn]);

    return allAnnotations;
};

export const getAnnotationElementId = (pageNum: number, elmId: string | number): string => {
    return `box-${pageNum}-${elmId}`;
};
