import { useCallback, useMemo, useRef, useState } from 'react';
import { cloneDeep, isEqual } from 'lodash';
import { Category, CategoryDataAttributeWithValue, Link } from 'api/typings';

import { Annotation } from 'shared';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import { getCategoryDataAttrs, isValidCategoryType, mapAnnDataAttrs } from './task-annotator-utils';
import { TUseAnnotationHandlersProps, UndoListAction } from './types';
import { scaleAnnotation } from 'shared/components/annotator/utils/scale-annotation';

export const useAnnotationHandlers = ({
    allAnnotations,
    setAllAnnotations,
    setModifiedPages,
    setTableMode,
    setSelectedAnnotation,
    setTabValue,
    categories,
    setIsCategoryDataEmpty,
    setAnnDataAttrs,
    currentPage,
    annotationsByUserId,
    setExternalViewer,
    createAnnotation,
    onAddTouchedPage
}: TUseAnnotationHandlersProps) => {
    const copiedAnnotationReference = useRef<Annotation>();
    const [undoPointer, setUndoPointer] = useState(-1);
    const [undoList, setUndoList] = useState<
        { action: UndoListAction; annotation: Annotation; pageNumber: number }[]
    >([]);

    const updateUndoList = (
        pageNum: number,
        annotationBeforeModification: Annotation | undefined,
        action: UndoListAction
    ) => {
        if (!annotationBeforeModification) {
            return;
        }
        const undoListCopy = cloneDeep(undoList);
        if (undoPointer !== -1) {
            undoListCopy.splice(undoPointer); // delete everything from pointer (including) to the right
            setUndoPointer(-1);
        }
        setUndoList([
            ...undoListCopy,
            { action, annotation: annotationBeforeModification, pageNumber: pageNum }
        ]);
    };

    const swapAnnotationState = (
        pageNumber: number,
        annotationId: number | string,
        undoPointer: number
    ) => {
        if (!allAnnotations) return;

        const oldAnnotationState = cloneDeep(
            allAnnotations[pageNumber].find((item) => item.id === annotationId)
        );

        modifyAnnotation(pageNumber, annotationId, undoList[undoPointer].annotation);

        const undoListCopy = cloneDeep(undoList);
        undoListCopy[undoPointer].annotation = oldAnnotationState!;
        setUndoList(undoListCopy);
    };

    const deleteAnnotation = (pageNum: number, annotationId: string | number) => {
        if (!allAnnotations) return;

        const pageAnnotation = allAnnotations[pageNum]?.find((el) => el.id === annotationId);

        if (!pageAnnotation) return;

        if (pageAnnotation?.labels) {
            const labelIndexToDelete = pageAnnotation.labels.findIndex(
                (item) => item.annotationId === annotationId
            );
            if (labelIndexToDelete !== -1) {
                // TODO: Don't modify array
                pageAnnotation?.labels?.splice(labelIndexToDelete, 1);
            }
        }

        setAllAnnotations((prevState) => {
            return {
                ...prevState,
                [pageNum]: prevState[pageNum].filter((ann) => {
                    if (
                        pageAnnotation.children &&
                        pageAnnotation.boundType === 'table' &&
                        pageAnnotation.children.includes(ann.id) &&
                        ann.boundType === 'table_cell'
                    ) {
                        return false;
                    }
                    return ann.id !== annotationId;
                })
            };
        });

        setModifiedPages((prevState) => {
            if (prevState.includes(pageNum)) return prevState;
            return [...prevState, pageNum];
        });
    };

    const modifyAnnotation = (
        pageNum: number,
        id: string | number,
        changes: Partial<Annotation>
    ) => {
        setAllAnnotations((prevState) => {
            let pageNumber: string | number = pageNum;

            if (pageNum === -1) {
                const annotationPage = Object.keys(prevState).find((key) =>
                    prevState[key].find((ann) => ann.id == id)
                );

                if (annotationPage) pageNumber = annotationPage;
            }

            const pageAnnotations = prevState[pageNumber] ?? [];

            return {
                ...prevState,
                [pageNumber]: pageAnnotations.map((ann) => {
                    if (ann.id === id) {
                        return { ...ann, ...changes, id };
                    }
                    return ann;
                })
            };
        });

        setModifiedPages((prevState) => {
            if (prevState.includes(pageNum)) return prevState;
            return [...prevState, pageNum];
        });
    };

    const findAndSetExternalViewerType = (
        annDataAttrs: CategoryDataAttributeWithValue[] | undefined
    ) => {
        const foundExternalViewer = annDataAttrs?.find(({ type }) => isValidCategoryType(type));

        if (foundExternalViewer) {
            setExternalViewer({
                isOpen: true,
                type: foundExternalViewer.type,
                name: foundExternalViewer.name,
                value: foundExternalViewer.value
            });
        }
    };

    const onAnnotationCreated = (pageNum: number, annData: Annotation, category?: Category) => {
        const newAnnotation = createAnnotation(pageNum, annData, category);

        // TODO: Do we really need clondeDeep here???
        updateUndoList(pageNum, cloneDeep(annData), 'add');
        return newAnnotation;
    };

    const onAnnotationDeleted = (pageNum: number, annotationId: string | number) => {
        if (!allAnnotations) return;

        const annotationBeforeModification = allAnnotations[pageNum]?.find(
            (item) => item.id === annotationId
        );

        // TODO: Do we really need clondeDeep here???
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'delete');
        deleteAnnotation(pageNum, annotationId);
    };

    const onAnnotationEdited = (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => {
        if (!allAnnotations) return;

        const annotationBeforeModification = allAnnotations[pageNum]?.find(
            (item) => item.id === annotationId
        );
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'edit');
        modifyAnnotation(pageNum, annotationId, changes);
    };

    const onAnnotationUndoPress = () => {
        let undoPointerCopy = undoPointer;
        if (!undoList.length || undoPointerCopy === 0) {
            return;
        }
        if (undoPointerCopy === -1) {
            undoPointerCopy = undoList.length - 1; // set initial pointer position
        } else {
            undoPointerCopy--; // move pointer one step to the left
        }

        const annotationId = undoList[undoPointerCopy].annotation.id;
        const pageNumber = undoList[undoPointerCopy].pageNumber;

        switch (undoList[undoPointerCopy].action) {
            case 'edit':
                swapAnnotationState(pageNumber, annotationId, undoPointerCopy);
                break;

            case 'delete':
                createAnnotation(pageNumber, undoList[undoPointerCopy].annotation);
                break;

            case 'add':
                deleteAnnotation(pageNumber, annotationId);
                break;
        }

        setUndoPointer(undoPointerCopy);
    };

    const onAnnotationRedoPress = () => {
        if (!undoList.length || undoPointer === -1) {
            return;
        }

        const annotationId = undoList[undoPointer].annotation.id;
        const pageNumber = undoList[undoPointer].pageNumber;

        switch (undoList[undoPointer].action) {
            case 'edit':
                swapAnnotationState(pageNumber, annotationId, undoPointer);
                break;

            case 'delete':
                deleteAnnotation(pageNumber, annotationId);
                break;

            case 'add':
                createAnnotation(pageNumber, undoList[undoPointer].annotation);
                break;
        }

        const isUndoPointerAtListEnd = undoPointer >= undoList.length - 1;
        setUndoPointer(isUndoPointerAtListEnd ? -1 : undoPointer + 1); // move pointer one step to the right if possible
    };

    const onAnnotationCopyPress = (pageNum: number, annotationId: string | number) => {
        if (allAnnotations && annotationId && pageNum) {
            const annotation = allAnnotations[pageNum].find((item) => item.id === annotationId);
            if (annotation) {
                copiedAnnotationReference.current = annotation;
            }
        }
    };

    const onAnnotationCutPress = (pageNum: number, annotationId: string | number) => {
        onAnnotationCopyPress(pageNum, annotationId);
        onAnnotationDeleted(pageNum, annotationId);
    };

    const onAnnotationPastePress = (pageSize: PageSize, pageNum: number) => {
        const annotationToPaste = copiedAnnotationReference.current;
        if (!annotationToPaste || !allAnnotations) {
            return;
        }

        const newAnnotation = cloneDeep(annotationToPaste);
        newAnnotation.bound.x = (pageSize?.width || 0) / 2 - newAnnotation.bound.width / 2;
        newAnnotation.bound.y = (pageSize?.height || 0) / 2 - newAnnotation.bound.height / 2;
        newAnnotation.id = Date.now();

        const pageAnnotations = allAnnotations[pageNum] ?? [];

        setAllAnnotations((prevState) => ({
            ...prevState,
            [pageNum]: [
                ...pageAnnotations,
                {
                    ...newAnnotation
                }
            ]
        }));
    };

    const onAnnotationDoubleClick = useCallback((annotation: Annotation) => {
        const { id, category } = annotation;

        if (annotation.boundType === 'table') {
            setTableMode(true);
            setTabValue('Data');
            setSelectedAnnotation(annotation);
            return;
        } else {
            setTableMode(false);
        }

        const foundCategoryDataAttrs = getCategoryDataAttrs(category, categories);

        if (foundCategoryDataAttrs) {
            setAnnDataAttrs((prevState) => {
                const mapAttributes = mapAnnDataAttrs(foundCategoryDataAttrs, prevState[id]);

                findAndSetExternalViewerType(mapAttributes);
                prevState[id] = mapAttributes;

                return prevState;
            });
            setIsCategoryDataEmpty(false);
            setSelectedAnnotation(annotation);
        } else {
            setIsCategoryDataEmpty(true);
            setSelectedAnnotation(undefined);
        }
    }, []);

    const onSplitAnnotationSelected = useCallback(
        (scale: number, userId: string, scaledAnn?: Annotation) => {
            if (!scaledAnn || !allAnnotations) {
                return;
            }

            const category = categories?.find((category) => category.id === scaledAnn.category);
            const originalAnn = annotationsByUserId[userId].find((ann) => ann.id === scaledAnn.id);

            if (!originalAnn) {
                return;
            }

            const copy = {
                ...cloneDeep(originalAnn),
                id: Date.now(),
                links: [],
                originalAnnotationId: Number(originalAnn.id)
            };

            const isExisted = allAnnotations[currentPage]?.some(
                ({ originalAnnotationId }) => originalAnnotationId === Number(originalAnn.id)
            );

            if (isExisted) {
                return;
            }

            const newAnn = onAnnotationCreated(currentPage, copy, category);
            setSelectedAnnotation(scaleAnnotation(newAnn, scale));
            onAddTouchedPage();
        },
        [categories, onAnnotationCreated, allAnnotations]
    );

    const onSplitLinkSelected = useCallback(
        (
            fromOriginalAnnotationId: string | number,
            originalLink: Link,
            annotations: Annotation[]
        ) => {
            if (!allAnnotations) return;

            const fromOriginalAnnotation =
                annotations.find(({ id }) => id === fromOriginalAnnotationId) || ({} as Annotation);
            const toOriginalAnnotation =
                annotations.find(({ id }) => id === originalLink.to) || ({} as Annotation);

            const fromUserAnnotation = allAnnotations[currentPage]?.find((annotation) =>
                fromOriginalAnnotation.boundType === 'text'
                    ? isEqual(annotation.tokens, fromOriginalAnnotation.tokens)
                    : isEqual(annotation.bound, fromOriginalAnnotation.bound)
            );

            const toUserAnnotation = allAnnotations[currentPage]?.find((annotation) =>
                toOriginalAnnotation.boundType === 'text'
                    ? isEqual(annotation.tokens, toOriginalAnnotation.tokens)
                    : isEqual(annotation.bound, toOriginalAnnotation.bound)
            );

            if (fromUserAnnotation && toUserAnnotation) {
                const fromUserLinks = fromUserAnnotation.links ?? [];
                const updatedLink = { ...originalLink, to: toUserAnnotation.id };

                const currentLinks = allAnnotations[currentPage]?.reduce(
                    (acc: Link[], { links = [] }) => [...acc, ...links],
                    []
                );

                const isExist = currentLinks.find((link) => isEqual(link, updatedLink));

                if (isExist) return;

                onAnnotationEdited(currentPage, fromUserAnnotation.id, {
                    links: [...fromUserLinks, updatedLink]
                });
            }
        },
        [allAnnotations]
    );

    return useMemo(
        () => ({
            onAnnotationCreated,
            onAnnotationDeleted,
            onAnnotationEdited,
            onAnnotationUndoPress,
            onAnnotationRedoPress,
            onAnnotationCopyPress,
            onAnnotationCutPress,
            onAnnotationPastePress,
            onAnnotationDoubleClick,
            onSplitAnnotationSelected,
            onSplitLinkSelected
        }),
        [
            onAnnotationCreated,
            onAnnotationDeleted,
            onAnnotationEdited,
            onAnnotationUndoPress,
            onAnnotationRedoPress,
            onAnnotationCopyPress,
            onAnnotationCutPress,
            onAnnotationPastePress,
            onAnnotationDoubleClick,
            onSplitAnnotationSelected,
            onSplitLinkSelected
        ]
    );
};
