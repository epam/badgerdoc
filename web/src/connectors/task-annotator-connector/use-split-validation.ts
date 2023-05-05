import { AnnotationsByUser, useLatestAnnotationsByUser } from 'api/hooks/annotations';
import { Category, Link, Taxon } from 'api/typings';
import { JobStatus, Job } from 'api/typings/jobs';
import cloneDeep from 'lodash/cloneDeep';
import isEqual from 'lodash/isEqual';
import { useCallback, useEffect, useMemo } from 'react';
import { Annotation } from 'shared';
import { scaleAnnotation } from 'shared/components/annotator/utils/scale-annotation';
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import { Task } from 'api/typings/tasks';
import { convertToUserRevisions } from './utils';
import { useGetPageSummary } from '../../api/hooks/tasks';
import { UserRevision } from './revisionTypes';

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
    taxonLabels: Map<string, Taxon>;
    onSplitAnnotationSelected: (scale: number, userId: string, annotation?: Annotation) => void;
    onSplitLinkSelected: (
        fromOriginalAnnotationId: string | number,
        originalLink: Link,
        annotations: Annotation[]
    ) => void;
    onFinishSplitValidation: () => void;
    latestRevisionByAnnotators: UserRevision[];
    latestRevisionByCurrentUser: UserRevision[];
    latestRevisionByAnnotatorsWithBounds: Record<string, Annotation[]>;
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

    const { data: pages } = useGetPageSummary(
        { taskId: task?.id, taskType: task?.is_validation },
        { enabled: Boolean(task) }
    );

    const { data: latestRevision } = useLatestAnnotationsByUser(
        {
            fileId,
            jobId: job?.id,
            pageNumbers: pages?.annotated_pages
        },
        { enabled: isSplitValidation }
    );

    const convertedLatestRevision = latestRevision ? convertToUserRevisions(latestRevision) : [];
    const currentUser = userId;

    const latestRevisionByAnnotators: UserRevision[] = useMemo(() => {
        return convertedLatestRevision.filter((revision) => revision.user_id !== currentUser);
    }, [latestRevision]);

    const latestRevisionByCurrentUser: UserRevision[] = useMemo(() => {
        return convertedLatestRevision.filter((revision) => revision.user_id === currentUser);
    }, [latestRevision]);

    const taxonLabels = useAnnotationsTaxons(latestRevisionByAnnotators);

    const { mapAnnotationPagesFromApi } = useAnnotationsMapper(taxonLabels, [byUser, taxonLabels]);

    const latestRevisionByAnnotatorsWithBounds = useMemo(() => {
        if (!latestRevisionByAnnotators) return {};
        return mapAnnotationPagesFromApi(
            (page: AnnotationsByUser) => page.user_id,
            latestRevisionByAnnotators,
            categories
        );
    }, [categories, mapAnnotationPagesFromApi, latestRevisionByAnnotators]);

    const onSplitAnnotationSelected = useCallback(
        (scale: number, userId: string, scaledAnn?: Annotation) => {
            if (!scaledAnn) {
                return;
            }

            let category: Category | undefined;
            const originalAnn = latestRevisionByAnnotatorsWithBounds[userId].find(
                (ann) => ann.id === scaledAnn.id
            );

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
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            onFinishSplitValidation,
            taxonLabels,
            latestRevisionByAnnotators,
            latestRevisionByCurrentUser,
            latestRevisionByAnnotatorsWithBounds
        }),
        [
            isSplitValidation,
            job,
            onSplitAnnotationSelected,
            onSplitLinkSelected,
            onAddTouchedPage,
            validatorAnnotations,
            taxonLabels,
            latestRevisionByAnnotators,
            latestRevisionByCurrentUser,
            latestRevisionByAnnotatorsWithBounds
        ]
    );
}
