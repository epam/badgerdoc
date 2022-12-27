import { AnnotationsByUserObj, useLatestAnnotationsByUser } from 'api/hooks/annotations';
import { useJobById } from 'api/hooks/jobs';
import { Category } from 'api/typings';
import { Job } from 'api/typings/jobs';
import { cloneDeep } from 'lodash';
import { useCallback, useMemo } from 'react';
import { Annotation, pageSizes } from 'shared';
import { downScaleCoords } from 'shared/components/annotator/utils/down-scale-coords';
import { scaleAnnotation } from 'shared/components/annotator/utils/scale-annotation';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';

interface SplitValidationParams {
    categories?: Category[];
    currentPage: number;
    fileId?: number;
    isValidation?: boolean;
    job?: Job;
    onAnnotationCreated: (
        pageNum: number,
        annotation: Annotation,
        category?: Category
    ) => Annotation;
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
}

export default function useSplitValidation({
    categories,
    currentPage,
    fileId,
    isValidation,
    job,
    onAnnotationCreated,
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

    const { mapAnnotationPagesFromApi } = useAnnotationsMapper([byUser]);

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

            const copy = cloneDeep(originalAnn);
            copy.id = Date.now();

            const newAnn = onAnnotationCreated(currentPage, copy, category);
            setSelectedAnnotation(scaleAnnotation(newAnn, scale));
            onAddTouchedPage();
            setValidPages([currentPage]);
        },
        [categories, onAnnotationCreated]
    );

    return useMemo(
        () => ({
            annotationsByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            userPages
        }),
        [
            annotationsByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onAddTouchedPage,
            userPages
        ]
    );
}
