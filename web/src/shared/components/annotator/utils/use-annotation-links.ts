import { Category, Link } from 'api/typings';
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
            JSON.stringify(prevSelected) !== JSON.stringify(selectedAnn)
        ) {
            const prevLinks = prevSelected.links ? prevSelected.links : [];
            let links = {
                links: [
                    ...prevLinks,
                    {
                        category_id: category?.id.toString(),
                        to: selectedAnn.id,
                        type: selectionType == 'Chain' ? 'directional' : 'omnidirectional',
                        page_num: current_page
                    } as Link
                ]
            };
            onAnnotationEdited(prevPage!, links, prevSelected.id);
        }
        setPrevSelected(selectedAnn);
        setPrevPage(current_page);
    }, [selectedAnn]);

    return allAnnotations;
};

export const getAnnotationElementId = (pageNum: number, elmId: string | number): string => {
    return `box-${pageNum}-${elmId}`;
};
