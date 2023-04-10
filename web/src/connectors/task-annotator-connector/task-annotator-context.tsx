import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useReducer,
    useRef
} from 'react';
import { cloneDeep } from 'lodash';
import { ApiError } from 'api/api-error';
import { useAddAnnotationsMutation, useLatestAnnotations } from 'api/hooks/annotations';
import { useSetTaskFinishedMutation, useSetTaskState, useTaskById } from 'api/hooks/tasks';
import { useCategoriesByJob } from 'api/hooks/categories';
import { useDocuments } from 'api/hooks/documents';
import { useJobById } from 'api/hooks/jobs';
import { useTokens } from 'api/hooks/tokens';
import {
    Category,
    CategoryDataAttributeWithValue,
    Label,
    Link,
    Operators,
    PageInfo,
    SortingDirection,
    Taxon
} from 'api/typings';

import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType,
    PageToken,
    PaperToolParams,
    TableGutterMap,
    ToolNames
} from 'shared';
import { useAnnotationsLinks } from 'shared/components/annotator/utils/use-annotation-links';
import { documentSearchResultMapper } from 'shared/helpers/document-search-result-mapper';
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import useSyncScroll from 'shared/hooks/use-sync-scroll';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import {
    getCategoryDataAttrs,
    isValidCategoryType,
    mapAnnDataAttrs,
    mapAnnotationDataAttrsFromApi,
    mapModifiedAnnotationPagesToApi,
    mapTokenPagesFromApi
} from './task-annotator-utils';
import useSplitValidation from './use-split-validation';
import { useDocumentLinks } from './use-document-links';
import { useValidation } from './use-validation';
import { useNotifications } from 'shared/components/notifications';

import { Text, Panel } from '@epam/loveship';
import { getError } from 'shared/helpers/get-error';
import { getToolsParams, reducer } from './utils';
import { ContextValue, ProviderProps, UndoListAction } from './types';
import {
    CHANGE_ANN_DATA_ATTRS,
    CLOSE_EXTERNAL_VIEWER,
    CREATE_ANNOTATION,
    DELETE_ANNOTATION,
    DELETE_ANNOTATION_LINK,
    INITIAL_STATE,
    MODIFY_ANNOTATION,
    ON_TABLE_DOUBLE_CLICK,
    SET_ALL_ANNOTATIONS,
    SET_ANN_DATA_ATTRS,
    SET_CURRENT_DOCUMENT_USER_ID,
    SET_CURRENT_PAGE,
    SET_EXTERNAL_VIEWER,
    SET_IS_NEED_TO_SAVE_TABLE,
    SET_LATEST_LABELS_ID,
    SET_MODIFIED_PAGES,
    SET_PAGE_SIZE,
    SET_SELECTED_ANNOTATION,
    SET_SELECTED_ANN_DATA_ATTRS,
    SET_SELECTED_CATEGORY,
    SET_SELECTED_LABELS,
    SET_SELECTED_TOOL,
    SET_SELECTED_TOOL_PARAMS,
    SET_SELECTION_TYPE,
    SET_STORED_PARAMS,
    SET_TABLE_CELL_CATEGORY,
    SET_TABLE_MODE,
    SET_TAB_VALUE,
    SET_UNDO_LIST,
    SET_UNDO_POINTER,
    SWAP_UNDO_LIST_ANNOTATION_STATE,
    UNSELECT_ANNOTATION
} from './constants';

const TaskAnnotatorContext = createContext<ContextValue | undefined>(undefined);

export const TaskAnnotatorContextProvider: React.FC<ProviderProps> = ({
    jobId,
    fileMetaInfo: fileMetaInfoParam,
    taskId,
    revisionId,
    onRedirectAfterFinish,
    onSaveTaskSuccess,
    onSaveTaskError,
    children
}) => {
    const [
        {
            currentDocumentUserId,
            selectedCategory,
            selectedLabels,
            latestLabelsId,
            isDocLabelsModified,
            allAnnotations,
            selectedToolParams,
            currentPage,
            modifiedPages,
            tabValue,
            selectionType,
            selectedTool,
            selectedAnnotation,
            isCategoryDataEmpty,
            annDataAttrs,
            externalViewer,
            tableMode,
            tableCellCategory,
            isNeedToSaveTable,
            storedParams,
            pageSize,
            undoList,
            undoPointer
        },
        dispatch
    ] = useReducer(reducer, INITIAL_STATE);

    const copiedAnnotationReference = useRef<Annotation | undefined>();

    const { notifyError } = useNotifications();

    const { data: task, isLoading: isTaskLoading, refetch: refetchTask } = useTaskById({ taskId });
    const { data: job } = useJobById({ jobId: task?.job.id });

    const getJobId = (): number | undefined => (task ? task.job.id : jobId); // Do we need this???

    const { data: { pages: categories } = {}, refetch: refetchCategories } = useCategoriesByJob(
        {
            jobId: getJobId(),
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );

    useEffect(() => {
        if (task?.job.id || jobId) {
            refetchCategories();
        }
    }, [task, jobId]);

    const documentsResult = useDocuments(
        {
            filters: [
                {
                    field: 'id',
                    operator: Operators.EQ,
                    value: task ? task.file.id : fileMetaInfoParam?.id
                }
            ]
        },
        { enabled: false }
    );

    const fileMetaInfo = useMemo(() => {
        if (fileMetaInfoParam) return fileMetaInfoParam;

        return {
            ...documentSearchResultMapper(documentsResult.data),
            isLoading: isTaskLoading || documentsResult.isLoading
        };
    }, [fileMetaInfoParam, documentsResult.data, documentsResult.isLoading, isTaskLoading]);

    const getFileId = (): number | undefined => (task ? task.file.id : fileMetaInfo?.id);

    const pageNumbers: number[] = useMemo(() => {
        if (task) return task.pages;
        if (fileMetaInfo.pages) {
            const pages = [];
            for (let i = 0; i < fileMetaInfo.pages; i++) {
                pages.push(i + 1);
            }

            return pages;
        }

        return [];
    }, [task?.pages, fileMetaInfo.pages]);

    const latestAnnotationsResult = useLatestAnnotations(
        {
            jobId: getJobId(),
            fileId: getFileId(),
            revisionId,
            pageNumbers: pageNumbers,
            userId:
                job?.validation_type === 'extensive_coverage' && !revisionId ? task?.user_id : ''
        },
        { enabled: Boolean(task || job) }
    );

    const tokenRes = useTokens(
        {
            fileId: getFileId(),
            pageNumbers: pageNumbers
        },
        { enabled: false }
    );
    const tokenPages = tokenRes.data;

    useEffect(() => {
        if (task || job || revisionId) {
            dispatch({ type: SET_CURRENT_PAGE, payload: pageNumbers[0] });
            documentsResult.refetch();
            latestAnnotationsResult.refetch();
            tokenRes.refetch();
        }
    }, [task, job, revisionId]);

    useAnnotationsLinks(
        selectedAnnotation,
        selectedCategory,
        currentPage,
        selectionType,
        allAnnotations,
        (prevPage, links, annId) => selectedAnnotation && onAnnotationEdited(prevPage, annId, links)
    );

    const createAnnotation = (
        pageNum: number,
        annData: Annotation,
        category = selectedCategory
    ): Annotation => {
        const hasTaxonomy = annData.data?.dataAttributes.some(
            ({ type }: CategoryDataAttributeWithValue) => type === 'taxonomy'
        );

        const annotation = {
            ...annData,
            categoryName: category?.name,
            color: category?.metadata?.color,
            label: hasTaxonomy ? annData.label : category?.name,
            labels: getAnnotationLabels(pageNum.toString(), annData, category)
        };

        dispatch({ type: CREATE_ANNOTATION, payload: { pageNum, annotation } });
        return annotation;
    };

    const onCloseDataTab = () => {
        dispatch({ type: SET_TAB_VALUE, payload: 'Categories' });
        onExternalViewerClose();
    };

    const onAnnotationCreated = (pageNum: number, annData: Annotation, category?: Category) => {
        const newAnnotation = createAnnotation(pageNum, annData, category);

        updateUndoList(pageNum, cloneDeep(annData), 'add');
        return newAnnotation;
    };

    const deleteAnnotation = (pageNum: number, annotationId: string | number) => {
        dispatch({ type: DELETE_ANNOTATION, payload: { pageNum, annotationId } });
    };

    const getAnnotationByIdAndPageNum = (annotationId: Annotation['id'], pageNum: number) =>
        (allAnnotations as Record<string, Annotation[]>)[pageNum]?.find(
            (item) => item.id === annotationId
        );

    const onAnnotationDeleted = (pageNum: number, annotationId: string | number) => {
        const annotationBeforeModification = getAnnotationByIdAndPageNum(annotationId, pageNum);
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'delete');

        deleteAnnotation(pageNum, annotationId);
    };

    const onCategorySelected = (category: Category) => {
        dispatch({ type: SET_SELECTED_CATEGORY, payload: category });
    };

    const onLabelsSelected = (labels: Label[]) => {
        if (!Array.isArray(labels)) return;

        dispatch({ type: SET_SELECTED_LABELS, payload: labels });
    };

    const onChangeSelectionType = (
        newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
    ) => {
        dispatch({ type: SET_SELECTION_TYPE, payload: newType });
    };

    const onChangeSelectedTool = (newTool: ToolNames) => {
        dispatch({ type: SET_SELECTED_TOOL, payload: newTool });
        onChangeSelectionType('polygon');
    };

    useEffect(() => {
        if (!selectedToolParams) return;

        dispatch({ type: SET_STORED_PARAMS, payload: selectedToolParams });
    }, [selectedToolParams]);

    useEffect(() => {
        const toolParams = getToolsParams(selectedTool, storedParams);

        if (toolParams) {
            dispatch({ type: SET_SELECTED_TOOL_PARAMS, payload: toolParams });
        }
    }, [selectedTool]);

    const onExternalViewerClose = () => {
        dispatch({ type: CLOSE_EXTERNAL_VIEWER, payload: undefined });
    };

    const findAndSetExternalViewerType = (
        annDataAttrs: CategoryDataAttributeWithValue[] | undefined
    ) => {
        const foundExternalViewer = annDataAttrs?.find(({ type }) => isValidCategoryType(type));

        if (foundExternalViewer) {
            dispatch({
                type: SET_EXTERNAL_VIEWER,
                payload: {
                    isOpen: true,
                    type: foundExternalViewer.type,
                    name: foundExternalViewer.name,
                    value: foundExternalViewer.value
                }
            });
        }
    };

    const onEmptyAreaClick = () => {
        dispatch({ type: UNSELECT_ANNOTATION, payload: undefined });
    };

    const setAnnotationDataAttrs = (annotation: Annotation) => {
        const foundCategoryDataAttrs = getCategoryDataAttrs(
            annotation.category ? annotation.category : annotation.label,
            categories
        );
        dispatch({
            type: SET_SELECTED_ANN_DATA_ATTRS,
            payload: { annotation, foundCategoryDataAttrs }
        });
    };

    const onAnnotationDoubleClick = (annotation: Annotation) => {
        const { id, category } = annotation;

        if (annotation.boundType === 'table') {
            dispatch({ type: ON_TABLE_DOUBLE_CLICK, payload: annotation });
            return;
        }

        const foundCategoryDataAttrs = getCategoryDataAttrs(category, categories);

        if (foundCategoryDataAttrs) {
            const mapAttributes = mapAnnDataAttrs(foundCategoryDataAttrs, annDataAttrs[id]);
            findAndSetExternalViewerType(mapAttributes);
        }

        dispatch({
            type: SET_SELECTED_ANN_DATA_ATTRS,
            payload: { annotation, foundCategoryDataAttrs }
        });
        dispatch({ type: SET_TABLE_MODE, payload: false });
    };

    useEffect(() => {
        if (!selectedAnnotation) return;

        setAnnotationDataAttrs(selectedAnnotation);
    }, [selectedAnnotation]);

    const onAnnotationCopyPress = (pageNum: number, annotationId: string | number) => {
        if (annotationId && pageNum) {
            const annotation = getAnnotationByIdAndPageNum(annotationId, pageNum);
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
        if (!copiedAnnotationReference.current) {
            return;
        }

        const newAnnotation = cloneDeep(copiedAnnotationReference.current);

        newAnnotation.id = Date.now();
        newAnnotation.bound.x = (pageSize?.width || 0) / 2 - newAnnotation.bound.width / 2;
        newAnnotation.bound.y = (pageSize?.height || 0) / 2 - newAnnotation.bound.height / 2;

        dispatch({ type: CREATE_ANNOTATION, payload: { pageNum, annotation: newAnnotation } });
    };

    // swap annotation state and its saved state in undoList
    const swapAnnotationState = (
        pageNumber: number,
        annotationId: number | string,
        undoPointer: number
    ) => {
        const oldAnnotationState = cloneDeep(getAnnotationByIdAndPageNum(annotationId, pageNumber));

        modifyAnnotation(pageNumber, annotationId, undoList[undoPointer].annotation);

        if (!oldAnnotationState) return;

        dispatch({
            type: SWAP_UNDO_LIST_ANNOTATION_STATE,
            payload: { annotation: oldAnnotationState, undoPointer }
        });
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

        dispatch({
            type: SET_UNDO_POINTER,
            payload: undoPointerCopy
        });
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
        dispatch({
            type: SET_UNDO_POINTER,
            payload: isUndoPointerAtListEnd ? -1 : undoPointer + 1
        });
    };

    const onDataAttributesChange = (index: number, value: string) => {
        dispatch({ type: CHANGE_ANN_DATA_ATTRS, payload: { index, value } });
    };

    const addAnnotationMutation = useAddAnnotationsMutation();

    const modifyAnnotation = (
        pageNum: number,
        id: string | number,
        changes: Partial<Annotation>
    ) => {
        dispatch({ type: MODIFY_ANNOTATION, payload: { pageNum, id, changes } });
    };

    const onLinkDeleted = (pageNum: number, annotationId: string | number, linkToDel: Link) => {
        dispatch({
            type: DELETE_ANNOTATION_LINK,
            payload: { pageNum, annotationId, link: linkToDel }
        });
    };

    const updateUndoList = (
        pageNum: number,
        annotationBeforeModification: Annotation | undefined,
        action: UndoListAction
    ) => {
        if (!annotationBeforeModification) {
            return;
        }
        const undoListCopy = [...undoList];

        if (undoPointer !== -1) {
            undoListCopy.splice(undoPointer); // delete everything from pointer (including) to the right
            dispatch({
                type: SET_UNDO_POINTER,
                payload: -1
            });
        }

        undoListCopy.push({
            action,
            pageNumber: pageNum,
            annotation: annotationBeforeModification
        });

        dispatch({ type: SET_UNDO_LIST, payload: undoListCopy });
    };

    const onAnnotationEdited = (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => {
        const annotationBeforeModification = getAnnotationByIdAndPageNum(annotationId, pageNum);
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'edit');
        modifyAnnotation(pageNum, annotationId, changes);
    };

    const { linksToApi, setDocumentLinksChanged, ...documentLinksValues } = useDocumentLinks(
        latestAnnotationsResult.data?.links_json
    );

    const onSaveTask = async () => {
        if (!task || !latestAnnotationsResult.data) return;

        let { revision, pages } = latestAnnotationsResult.data;

        const selectedLabelsId = selectedLabels.map((obj) => obj.id) ?? [];

        onCloseDataTab();

        if (task.is_validation && !splitValidation.isSplitValidation) {
            setAnnotationSaved(true);
            pages = pages.filter(
                (page) => validPages.includes(page.page_num) || invalidPages.includes(page.page_num)
            );
        } else {
            pages = mapModifiedAnnotationPagesToApi(
                modifiedPages,
                allAnnotations,
                tokensByPages,
                tokenPages?.length ? tokenPages : pages,
                annDataAttrs,
                pageSize
            );
        }

        if (!taskId) {
            return;
        }

        try {
            await addAnnotationMutation.mutateAsync({
                taskId,
                pages: validPages.length || invalidPages.length ? [] : pages,
                userId: task.user_id,
                revision,
                validPages: validPages,
                invalidPages: invalidPages,
                selectedLabelsId,
                links: linksToApi
            });
            onSaveTaskSuccess?.();
            latestAnnotationsResult.refetch();
            refetchTask();
            setDocumentLinksChanged?.(false);
        } catch (error) {
            onSaveTaskError?.(error as ApiError);
        }
    };
    const tokensByPages = useMemo<Record<string, PageToken[]>>(() => {
        if (!tokenPages?.length) {
            return {};
        }
        const tokenScale =
            pageSize && tokenPages[0].size && tokenPages[0].size.width
                ? pageSize.width / tokenPages[0].size?.width!
                : 1;
        return mapTokenPagesFromApi(tokenPages, tokenScale);
    }, [tokenPages, pageSize]);

    const {
        validPages,
        invalidPages,
        onAddTouchedPage,
        setValidPages,
        setAnnotationSaved,
        ...validationValues
    } = useValidation({
        latestAnnotationsResult,
        task,
        currentPage,
        jobUsers: {
            owners: job?.owners ?? [],
            annotators: job?.annotators ?? [],
            validators: job?.validators ?? []
        },
        onCloseDataTab,
        onSaveTask,
        allAnnotations,
        tokensByPages,
        tokenPages,
        annDataAttrs,
        pageSize,
        onRedirectAfterFinish,
        onSaveTaskSuccess,
        onSaveTaskError
    });

    const finishTaskMutation = useSetTaskFinishedMutation();
    const onAnnotationTaskFinish = async () => {
        if (task) {
            try {
                await onSaveTask();
                await finishTaskMutation.mutateAsync({ taskId: task!.id }).catch((e) => {
                    notifyError(
                        <Panel>
                            <Text>{`Can't finish task: ${getError(e)}`}</Text>
                        </Panel>
                    );
                });

                useSetTaskState({ id: task!.id, eventType: 'closed' });
                onRedirectAfterFinish?.();
            } catch {
                (e: Error) => {
                    console.error(e);
                };
            }
        }
    };

    const onCurrentPageChange = (page: number) => {
        dispatch({ type: SET_CURRENT_PAGE, payload: page });
    };

    const splitValidation = useSplitValidation({
        categories: categories,
        currentPage,
        fileId: getFileId(),
        isValidation: task?.is_validation,
        job,
        validatorAnnotations: allAnnotations,
        onAnnotationCreated,
        onAnnotationEdited,
        onAddTouchedPage: onAddTouchedPage,
        setSelectedAnnotation: (annotation?: Annotation) => {
            dispatch({ type: SET_SELECTED_ANNOTATION, payload: annotation });
        },
        validPages: validPages,
        setValidPages: setValidPages,
        onAnnotationTaskFinish,
        userId: task?.user_id,
        task: task
    });
    const taxonLabels = useAnnotationsTaxons(latestAnnotationsResult.data?.pages);
    const comparedTaxonLabels: Map<string, Taxon> = useMemo(
        () => new Map([...taxonLabels, ...splitValidation.taxonLabels]),
        [taxonLabels, splitValidation.taxonLabels]
    );
    const { getAnnotationLabels, mapAnnotationPagesFromApi } = useAnnotationsMapper(
        comparedTaxonLabels,
        [latestAnnotationsResult.data?.pages, comparedTaxonLabels]
    );

    useEffect(() => {
        if (!latestAnnotationsResult.data || !categories) return;
        const {
            categories: latestLabelIds,
            pages,
            pages: [firstPage]
        } = latestAnnotationsResult.data;

        if (latestLabelIds) {
            dispatch({ type: SET_LATEST_LABELS_ID, payload: latestLabelIds });
        }

        const result = mapAnnotationPagesFromApi(
            (page: PageInfo) => page.page_num.toString(),
            pages,
            categories
        );

        dispatch({ type: SET_ALL_ANNOTATIONS, payload: result });

        const annDataAttrsResult = mapAnnotationDataAttrsFromApi(
            latestAnnotationsResult.data.pages
        );

        dispatch({ type: SET_ANN_DATA_ATTRS, payload: annDataAttrsResult });

        if (firstPage?.size?.width && firstPage?.size?.height) {
            dispatch({ type: SET_PAGE_SIZE, payload: firstPage.size });
        }
    }, [latestAnnotationsResult.data, categories, mapAnnotationPagesFromApi]);

    const onClearModifiedPages = useCallback(async () => {
        dispatch({ type: SET_MODIFIED_PAGES, payload: [] });
    }, []);

    const syncScroll = useSyncScroll();

    const value = useMemo<ContextValue>(() => {
        return {
            task,
            job,
            getJobId,
            categories,
            selectedCategory,
            fileMetaInfo,
            tokensByPages,
            allAnnotations,
            pageNumbers,
            currentPage,
            pageSize,
            modifiedPages,
            selectionType,
            selectedTool,
            selectedToolParams,
            onChangeSelectedTool,
            tableMode,
            isNeedToSaveTable,
            tabValue,
            selectedAnnotation,
            isCategoryDataEmpty,
            annDataAttrs,
            externalViewer,
            tableCellCategory,
            setSelectedAnnotation: (annotation?: Annotation) => {
                dispatch({ type: SET_SELECTED_ANNOTATION, payload: annotation });
            },
            setTabValue: (tabValue: string) => {
                dispatch({ type: SET_TAB_VALUE, payload: tabValue });
            },
            setPageSize: (pageSize: { width: number; height: number }) => {
                dispatch({ type: SET_PAGE_SIZE, payload: pageSize });
            },
            setSelectedToolParams: (toolParams: PaperToolParams) => {
                dispatch({ type: SET_SELECTED_TOOL_PARAMS, payload: toolParams });
            },
            setIsNeedToSaveTable: (value: { gutters?: TableGutterMap; cells?: Annotation[] }) => {
                dispatch({ type: SET_IS_NEED_TO_SAVE_TABLE, payload: value });
            },
            setTableCellCategory: (cellCategory: string | number | undefined) => {
                dispatch({ type: SET_TABLE_CELL_CATEGORY, payload: cellCategory });
            },
            setCurrentDocumentUserId: (documentId?: string) => {
                dispatch({ type: SET_CURRENT_DOCUMENT_USER_ID, payload: documentId });
            },
            onAnnotationCreated,
            onAnnotationDeleted,
            onAnnotationEdited,
            onLinkDeleted,
            onCategorySelected,
            onChangeSelectionType,
            onSaveTask,
            onAnnotationTaskFinish,
            onCurrentPageChange,
            onClearModifiedPages,
            onDataAttributesChange,
            onEmptyAreaClick,
            onAnnotationDoubleClick,
            onAnnotationCopyPress,
            onAnnotationCutPress,
            onAnnotationPastePress,
            onAnnotationUndoPress,
            onAnnotationRedoPress,
            onExternalViewerClose,
            selectedLabels,
            onLabelsSelected,
            isDocLabelsModified,
            latestLabelsId,
            currentDocumentUserId,
            validPages,
            invalidPages,
            onAddTouchedPage,
            setValidPages,
            ...validationValues,
            ...splitValidation,
            ...syncScroll,
            ...documentLinksValues
        };
    }, [
        task,
        job,
        categories,
        selectedCategory,
        selectionType,
        selectedTool,
        fileMetaInfo,
        tokensByPages,
        allAnnotations,
        currentPage,
        pageSize,
        tableMode,
        isNeedToSaveTable,
        tabValue,
        selectedAnnotation,
        annDataAttrs,
        externalViewer,
        tableCellCategory,
        selectedToolParams,
        splitValidation,
        syncScroll,
        selectedLabels,
        latestLabelsId,
        documentLinksValues,
        latestAnnotationsResult,
        validPages,
        invalidPages,
        onAddTouchedPage,
        setValidPages,
        currentDocumentUserId
    ]);

    return <TaskAnnotatorContext.Provider value={value}>{children}</TaskAnnotatorContext.Provider>;
};

export const useTaskAnnotatorContext = () => {
    const context = useContext(TaskAnnotatorContext);

    if (context === undefined) {
        throw new Error(
            `useTaskAnnotatorContext must be used within a TaskAnnotatorContextProvider`
        );
    }
    return context;
};
