import { AnnotationsByUserObj, useLatestAnnotationsByUser } from 'api/hooks/annotations';
import { Category, Label, Link, Taxon } from 'api/typings';
import { Job, JobStatus } from 'api/typings/jobs';
import cloneDeep from 'lodash/cloneDeep';
import isEqual from 'lodash/isEqual';
import { useCallback, useEffect, useMemo } from 'react';
import { Annotation } from 'shared';
import { scaleAnnotation } from 'shared/components/annotator/utils/scale-annotation';
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import { Task } from 'api/typings/tasks';

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
    validPages: number[];
    setValidPages: (pages: number[]) => void;
    onAnnotationTaskFinish: () => void;
    userId?: string;
    task?: Task;
}

export interface SplitValidationValue {
    isSplitValidation?: boolean;
    userPages: AnnotationsByUserObj[];
    annotationsByUserId: Record<string, Annotation[]>;
    categoriesByUserId: Record<string, Label[]>;
    taxonLabels: Map<string, Taxon>;
    onSplitAnnotationSelected: (scale: number, userId: string, annotation?: Annotation) => void;
    onSplitLinkSelected: (
        fromOriginalAnnotationId: string | number,
        originalLink: Link,
        annotations: Annotation[]
    ) => void;
    onFinishSplitValidation: () => void;
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
    validPages,
    onAnnotationTaskFinish,
    userId,
    task
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

    const getCategoryById = useCallback(
        (categoryId: string): Label | undefined => {
            const category = categories!.find(({ id }) => id === categoryId);

            if (!category) return;

            const { id, name } = category;

            return { id, name };
        },
        [categories]
    );

    const categoriesByUserId: Record<string, Label[]> = useMemo(() => {
        if (!categories?.length) return {};

        return userPages.reduce(
            (acc, { user_id, categories: categoriesId }) => ({
                ...acc,
                [user_id]: categoriesId.map(getCategoryById) as Label[]
            }),
            {} as Record<string, Label[]>
        );
    }, [userPages, categories, getCategoryById]);

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
            if (
                validatorAnnotations[currentPage]
                    ?.map((el) => el.originalAnnotationId)
                    .includes(Number(originalAnn.id))
            ) {
                return;
            }

            const newAnn = onAnnotationCreated(currentPage, copy, category);
            setSelectedAnnotation(scaleAnnotation(newAnn, scale));
            onAddTouchedPage();
        },
        [categories, onAnnotationCreated, validatorAnnotations]
    );

    const onSplitLinkSelected = useCallback(
        (
            fromOriginalAnnotationId: string | number,
            originalLink: Link,
            annotations: Annotation[]
        ) => {
            const fromOriginalAnnotation =
                annotations.find(({ id }) => id === fromOriginalAnnotationId) || ({} as Annotation);
            const toOriginalAnnotation =
                annotations.find(({ id }) => id === originalLink.to) || ({} as Annotation);

            const fromUserAnnotation = validatorAnnotations[currentPage]?.find((annotation) =>
                fromOriginalAnnotation.boundType === 'text'
                    ? isEqual(annotation.tokens, fromOriginalAnnotation.tokens)
                    : isEqual(annotation.bound, fromOriginalAnnotation.bound)
            );

            const toUserAnnotation = validatorAnnotations[currentPage]?.find((annotation) =>
                toOriginalAnnotation.boundType === 'text'
                    ? isEqual(annotation.tokens, toOriginalAnnotation.tokens)
                    : isEqual(annotation.bound, toOriginalAnnotation.bound)
            );

            if (fromUserAnnotation && toUserAnnotation) {
                const fromUserLinks = fromUserAnnotation.links ?? [];
                const updatedLink = { ...originalLink, to: toUserAnnotation.id };

                const currentLinks = validatorAnnotations[currentPage]?.reduce(
                    (acc, { links = [] }) => [...acc, ...links],
                    [] as Link[]
                );

                const isExist = currentLinks.find((link) => isEqual(link, updatedLink));

                if (isExist) return;

                onAnnotationEdited(currentPage, fromUserAnnotation.id, {
                    links: [...fromUserLinks, updatedLink]
                });
            }
        },
        [validatorAnnotations]
    );
    const onFinishSplitValidation = () => {
        if (!task || !isSplitValidation) return;
        setValidPages(task?.pages!);
    };

    useEffect(() => {
        if (validPages.length && isSplitValidation && job.status !== JobStatus.Finished) {
            onAnnotationTaskFinish();
        }
    }, [validPages, isSplitValidation]);

    return useMemo(
        () => ({
            annotationsByUserId,
            categoriesByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            onFinishSplitValidation,
            userPages,
            taxonLabels
        }),
        [
            annotationsByUserId,
            categoriesByUserId,
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            onAddTouchedPage,
            userPages,
            validatorAnnotations,
            taxonLabels
        ]
    );
}
