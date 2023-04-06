import { Category } from 'api/typings';
import { useEffect, useState } from 'react';
import { Annotation, AnnotationBoundType, AnnotationLinksBoundType, ToolNames } from 'shared';

export type AnnotationLink = {
    prevSelected: Annotation;
    linkedWith: Annotation;
};

export const useAnnotationsLinks = (
    selectedAnn: Annotation | undefined,
    category: Category | undefined,
    current_page: number | undefined,
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames,
    allAnnotations: Record<number, Annotation[]>,
    onAnnotationEdited: (
        prevPage: number,
        annId: number | string,
        links: Pick<Annotation, 'links'>
    ) => void
) => {
    const [prevSelected, setPrevSelected] = useState<Annotation | undefined>();
    const [prevPage, setPrevPage] = useState<number>();

    useEffect(() => {
        if (['box', 'free-box', 'table', 'table-cell', 'text'].includes(selectionType)) {
            setPrevSelected(undefined);
            setPrevPage(undefined);
            return;
        }
        //TODO: replace JSON.stringify with check of pageNum and id
        if (
            prevSelected !== undefined &&
            selectedAnn &&
            category &&
            current_page &&
            JSON.stringify(prevSelected) !== JSON.stringify(selectedAnn)
        ) {
            const links = prevSelected.links ? [...prevSelected.links] : [];

            links.push({
                to: selectedAnn.id,
                page_num: current_page,
                category_id: category?.id.toString(),
                type: selectionType === 'Chain' ? 'directional' : 'omnidirectional'
            });

            onAnnotationEdited(prevPage!, prevSelected.id, { links });
        }

        setPrevSelected(selectedAnn);
        setPrevPage(current_page);
    }, [selectedAnn]);

    return allAnnotations;
};

export const getAnnotationElementId = (pageNum: number, elmId: string | number): string => {
    return `box-${pageNum}-${elmId}`;
};
