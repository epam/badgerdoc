import { AnnotationsByUserObj, useLatestAnnotationsByUser } from 'api/hooks/annotations';
import { Category, Link } from 'api/typings';
import { Job } from 'api/typings/jobs';
import { cloneDeep } from 'lodash';
import { useCallback, useMemo } from 'react';
import { Annotation } from 'shared';
import { scaleAnnotation } from 'shared/components/annotator/utils/scale-annotation';
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';

interface SplitValidationParams {
    categories?: Category[];
    currentPage: number;
    fileId?: number;
    isValidation?: boolean;
    job?: Job;
    validatorAnnotations: Record<number, Annotation[]>;
    onAnnotationCreated: (
        pageNum: number,
        annotation: Annotation,
        category?: Category
    ) => Annotation;
    onAnnotationEdited: (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => void;
    onAddTouchedPage: () => void;
    setSelectedAnnotation: (ann: Annotation | undefined) => void;
    setValidPages: (pages: number[]) => void;
    userId?: string;
}

export interface SplitValidationValue {
    isSplitValidation?: boolean;
    userPages: AnnotationsByUserObj[];
    annotationsByUserId: Record<string, Annotation[]>;
    onSplitAnnotationSelected: (scale: number, userId: string, annotation?: Annotation) => void;
    onSplitLinkSelected: (fromOriginalAnnotationId: string | number, originalLink: Link) => void;
}

export default function useSplitValidation({
    categories,
    currentPage,
    fileId,
    isValidation,
    job,
    validatorAnnotations,
    onAnnotationCreated,
    onAnnotationEdited,
    onAddTouchedPage,
    setSelectedAnnotation,
    setValidPages,
    userId
}: SplitValidationParams): SplitValidationValue {
    const isSplitValidation = isValidation && job?.validation_type === 'extensive_coverage';

    const { data: byUser } = useLatestAnnotationsByUser(
        {
            fileId,
            jobId: job?.id,
            pageNumbers: [currentPage]
        },
        { enabled: isSplitValidation }
    );

    const userPages: AnnotationsByUserObj[] = useMemo(() => {
        if (!byUser) {
            return [];
        }
        return byUser[currentPage].filter((userPage) => userPage.user_id !== userId);
    }, [byUser, currentPage]);

    const taxonLabels = useAnnotationsTaxons(userPages);

    const { mapAnnotationPagesFromApi } = useAnnotationsMapper(taxonLabels, [byUser, taxonLabels]);

    const annotationsByUserId = useMemo(() => {
        return mapAnnotationPagesFromApi(
            (page: AnnotationsByUserObj) => page.user_id,
            userPages,
            categories
        );
    }, [categories, mapAnnotationPagesFromApi]);

    const onSplitAnnotationSelected = useCallback(
        (scale: number, userId: string, scaledAnn?: Annotation) => {
            if (!scaledAnn) {
                return;
            }

            let category: Category | undefined;
            const originalAnn = annotationsByUserId[userId].find((ann) => ann.id === scaledAnn.id);

            if (categories) {
                category = categories.find((category) => category.id === scaledAnn.category);
            }

            if (!originalAnn) {
                return;
            }

            const copy = {
                ...cloneDeep(originalAnn),
                links: [],
                originalAnnotationId: Number(originalAnn.id)
            };
            copy.id = Date.now();

            const newAnn = onAnnotationCreated(currentPage, copy, category);
            setSelectedAnnotation(scaleAnnotation(newAnn, scale));
            onAddTouchedPage();
            setValidPages([currentPage]);
        },
        [categories, onAnnotationCreated]
    );

    const onSplitLinkSelected = useCallback(
        (fromOriginalAnnotationId: string | number, originalLink: Link) => {
            const fromUserAnnotation = validatorAnnotations[currentPage].find(
                (annotation) => annotation.originalAnnotationId === fromOriginalAnnotationId
            );
            const toUserAnnotation = validatorAnnotations[currentPage].find(
                (annotation) => annotation.originalAnnotationId === originalLink.to
            );

            if (fromUserAnnotation && toUserAnnotation) {
                const fromUserLinks = fromUserAnnotation.links ?? [];

                onAnnotationEdited(currentPage, fromUserAnnotation.id, {
                    links: [...fromUserLinks, { ...originalLink, to: toUserAnnotation.id }]
                });
            }
        },
        [validatorAnnotations]
    );

    return useMemo(
        () => ({
            annotationsByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            userPages
        }),
        [
            annotationsByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            onAddTouchedPage,
            userPages,
            validatorAnnotations
        ]
    );
}
