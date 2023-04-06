import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ApiError } from 'api/api-error';
import {
    AnnotationsByUserObj,
    useAddAnnotationsMutation,
    useLatestAnnotations,
    useLatestAnnotationsByUser
} from 'api/hooks/annotations';
import { useSetTaskFinishedMutation, useSetTaskState, useTaskById } from 'api/hooks/tasks';
import { useCategoriesByJob } from 'api/hooks/categories';
import { useDocuments } from 'api/hooks/documents';
import { useJobById } from 'api/hooks/jobs';
import { useTokens } from 'api/hooks/tokens';
import {
    Category,
    CategoryDataAttributeWithValue,
    ExternalViewerState,
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
    AnnotationLinksBoundType,
    Maybe,
    PageToken,
    PaperToolParams,
    TableGutterMap,
    ToolNames
} from 'shared';
import { documentSearchResultMapper } from 'shared/helpers/document-search-result-mapper';
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import useSyncScroll from 'shared/hooks/use-sync-scroll';
import {
    defaultExternalViewer,
    getCategoryDataAttrs,
    isValidCategoryType,
    mapAnnDataAttrs,
    mapAnnotationDataAttrsFromApi,
    mapModifiedAnnotationPagesToApi,
    mapTokenPagesFromApi
} from './task-annotator-utils';
import { useDocumentLinks } from './use-document-links';
import { useValidation } from './use-validation';
import { useNotifications } from 'shared/components/notifications';

import { Text, Panel } from '@epam/loveship';
import { getError } from 'shared/helpers/get-error';
import { DEFAULT_PAGE_HEIGHT, DEFAULT_PAGE_WIDTH, DEFAULT_STORED_PARAMS } from './constants';
import { getToolsParams, mapCategoriesIdToCategories } from './utils';
import { ContextValue, ProviderProps } from './types';
import { useAnnotationHandlers } from './use-annotation-handlers';
import { JobStatus } from 'api/typings/jobs';
import { useAnnotationsLinks } from 'shared/components/annotator/utils/use-annotation-links';

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
    const [currentDocumentUserId, setCurrentDocumentUserId] = useState<string>();
    const [selectedCategory, setSelectedCategory] = useState<Category>();
    const [selectedLabels, setSelectedLabels] = useState<Label[]>([]);
    const [latestLabelsId, setLatestLabelsId] = useState<string[]>([]);
    const [isDocLabelsModified, setIsDocLabelsModified] = useState<boolean>(false);
    const [allAnnotations, setAllAnnotations] = useState<Record<string, Annotation[]>>({});
    const [selectedToolParams, setSelectedToolParams] = useState<PaperToolParams>(
        {} as PaperToolParams
    );

    const [currentPage, setCurrentPage] = useState<number>(1);

    const [modifiedPages, setModifiedPages] = useState<number[]>([]);
    const [tabValue, setTabValue] = useState<string>('Categories');
    const [selectionType, setSelectionType] = useState<
        AnnotationBoundType | AnnotationLinksBoundType | ToolNames
    >('free-box');
    const [selectedTool, setSelectedTool] = useState<ToolNames>(ToolNames.pen);
    const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | undefined>();
    const [isCategoryDataEmpty, setIsCategoryDataEmpty] = useState<boolean>(false);
    const [annDataAttrs, setAnnDataAttrs] = useState<
        Record<string, Array<CategoryDataAttributeWithValue>>
    >({});
    const [externalViewer, setExternalViewer] =
        useState<ExternalViewerState>(defaultExternalViewer);

    const [tableMode, setTableMode] = useState<boolean>(false);
    const [tableCellCategory, setTableCellCategory] = useState<string | number | undefined>('');

    const [isNeedToSaveTable, setIsNeedToSaveTable] = useState<{
        gutters: Maybe<TableGutterMap>;
        cells: Maybe<Annotation[]>;
    }>({
        gutters: undefined,
        cells: undefined
    });

    const [storedParams, setStoredParams] =
        useState<Record<ToolNames, PaperToolParams | undefined>>(DEFAULT_STORED_PARAMS);

    const [pageSize, setPageSize] = useState<{ width: number; height: number }>({
        width: DEFAULT_PAGE_WIDTH,
        height: DEFAULT_PAGE_HEIGHT
    });

    const { notifyError } = useNotifications();

    const { data: task, isLoading: isTaskLoading, refetch: refetchTask } = useTaskById({ taskId });
    const { data: job } = useJobById({ jobId: task?.job.id });

    const isSplitValidation = Boolean(
        task?.user_id && job?.validation_type === 'extensive_coverage'
    );
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

    const fileId = task ? task.file.id : fileMetaInfo?.id; // Do we need this???

    const pageNumbers: number[] = useMemo(() => {
        if (task) return task.pages;
        if (fileMetaInfo?.pages) {
            const pages = [];
            for (let i = 0; i < fileMetaInfo.pages; i++) {
                pages.push(i + 1);
            }

            return pages;
        }

        return [];
    }, [task?.pages, fileMetaInfo?.pages]);

    const latestAnnotationsResult = useLatestAnnotations(
        {
            jobId: getJobId(),
            fileId,
            revisionId,
            pageNumbers: pageNumbers,
            userId:
                job?.validation_type === 'extensive_coverage' && !revisionId ? task?.user_id : ''
        },
        { enabled: Boolean(task || job) }
    );

    const { data: tokenPages, refetch: refetchTokens } = useTokens(
        {
            fileId,
            pageNumbers: pageNumbers
        },
        { enabled: false }
    );

    const { data: annotationsByPage } = useLatestAnnotationsByUser(
        {
            jobId: job?.id,
            pageNumbers: [currentPage],
            fileId: task ? task.file.id : fileMetaInfo?.id
        },
        { enabled: true }
    );

    const notTaskUserPages: AnnotationsByUserObj[] = useMemo(() => {
        if (!annotationsByPage) {
            return [];
        }
        return annotationsByPage[currentPage].filter((page) => page.user_id !== task?.user_id);
    }, [annotationsByPage, currentPage, task]);

    const notTaskUserPagesTaxonLabels = useAnnotationsTaxons(notTaskUserPages);

    const notTaskUserPagesMapper = useAnnotationsMapper(notTaskUserPagesTaxonLabels, [
        notTaskUserPages,
        notTaskUserPagesTaxonLabels
    ]);

    const notTaskUserAnnotationsByUserId = useMemo(() => {
        return notTaskUserPagesMapper.mapAnnotationPagesFromApi(
            (page: AnnotationsByUserObj) => page.user_id,
            notTaskUserPages,
            categories
        );
    }, [categories, notTaskUserPagesMapper.mapAnnotationPagesFromApi]);

    const categoriesByUserId = useMemo(() => {
        if (!categories?.length) return {};

        return notTaskUserPages.reduce(
            (accumulator: Record<string, Label[]>, { user_id, categories: categoriesIds }) => {
                accumulator[user_id] = mapCategoriesIdToCategories(categoriesIds, categories);
                return accumulator;
            },
            {}
        );
    }, [notTaskUserPages, categories]);

    const addAnnotationMutation = useAddAnnotationsMutation();

    useEffect(() => {
        if (task?.job.id || jobId) {
            refetchCategories();
        }
    }, [task, jobId]);

    useEffect(() => {
        if (task || job || revisionId) {
            setCurrentPage(pageNumbers[0]);
            documentsResult.refetch();
            latestAnnotationsResult.refetch();
            refetchTokens();
        }
    }, [task, job, revisionId]);

    useEffect(() => {
        setStoredParams({
            ...storedParams,
            [selectedTool]: selectedToolParams
        });
    }, [selectedToolParams]);

    useEffect(() => {
        const toolParams = getToolsParams(selectedTool, storedParams);

        if (toolParams) {
            setSelectedToolParams(toolParams);
        }
    }, [selectedTool]);

    useEffect(() => {
        if (!selectedAnnotation) return;

        setAnnotationDataAttrs(selectedAnnotation);
    }, [selectedAnnotation]);

    const onCloseDataTab = () => {
        setTabValue('Categories');
        onExternalViewerClose();
    };

    const onCategorySelected = (category: Category) => {
        setSelectedCategory(category);
    };

    const onLabelsSelected = (labels: Label[], pickedLabels: string[]) => {
        if (!Array.isArray(labels)) return;

        const currentLabelsId = labels.map((label) => label.id);
        const isDocLabelsModifiedNewVal = latestLabelsId.toString() === currentLabelsId.toString();

        setIsDocLabelsModified(isDocLabelsModifiedNewVal);

        setSelectedLabels((prev) => {
            const combinedLabels = [...prev, ...labels];
            // TODO: Do we really need to use Map here???
            const arrayUniqueByKey = [
                ...new Map(combinedLabels.map((item) => [item.id, item])).values()
            ].filter((label) => pickedLabels.includes(label.id));
            return arrayUniqueByKey;
        });
    };

    const onChangeSelectionType = (
        newType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames
    ) => {
        setSelectionType(newType);
    };

    const onChangeSelectedTool = (newTool: ToolNames) => {
        setSelectedTool(newTool);
        setSelectionType('polygon');
    };

    const onExternalViewerClose = () => setExternalViewer(defaultExternalViewer);

    const onEmptyAreaClick = () => {
        setIsCategoryDataEmpty(true);
        setTabValue('Categories');
        setSelectedAnnotation(undefined);
    };

    const setAnnotationDataAttrs = (annotation: Annotation) => {
        const foundCategoryDataAttrs = getCategoryDataAttrs(
            annotation.category ? annotation.category : annotation.label,
            categories
        );
        if (foundCategoryDataAttrs && foundCategoryDataAttrs.length) {
            setAnnDataAttrs((prevState) => {
                prevState[annotation.id] = mapAnnDataAttrs(
                    foundCategoryDataAttrs,
                    prevState[annotation.id]
                );
                return prevState;
            });
            setTabValue('Data');
            setIsCategoryDataEmpty(false);
            setSelectedAnnotation(annotation);
        } else {
            setTabValue('Categories');
            setIsCategoryDataEmpty(true);
        }
    };

    const onDataAttributesChange = (elIndex: number, value: string) => {
        const newAnn = { ...annDataAttrs };

        if (selectedAnnotation) {
            const annItem = newAnn[selectedAnnotation.id][elIndex];
            newAnn[selectedAnnotation.id][elIndex].value = value;

            if (isValidCategoryType(annItem.type)) {
                setExternalViewer({
                    isOpen: true,
                    type: annItem.type,
                    name: annItem.name,
                    value
                });
            }
            setAnnDataAttrs(newAnn);
        }
    };

    const onLinkDeleted = (pageNum: number, id: string | number, linkToDel: Link) => {
        setAllAnnotations((prevState) => {
            const pageAnnotations = prevState[pageNum] ?? [];
            return {
                ...prevState,
                [pageNum]: pageAnnotations.map((ann) => {
                    if (ann.id === id) {
                        return {
                            ...ann,
                            links: ann.links?.filter((link) => {
                                return (
                                    link.category_id !== linkToDel.category_id &&
                                    link.page_num !== linkToDel.page_num &&
                                    link.to !== linkToDel.to &&
                                    link.type !== linkToDel.type
                                );
                            })
                        };
                    }
                    return ann;
                })
            };
        });
    };

    const { linksToApi, setDocumentLinksChanged, ...documentLinksValues } = useDocumentLinks(
        latestAnnotationsResult.data?.links_json
    );

    const onSaveTask = async () => {
        if (!task || !latestAnnotationsResult.data) return;

        let { revision, pages } = latestAnnotationsResult.data;

        onCloseDataTab();

        if (task.is_validation && !isSplitValidation) {
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

        try {
            await addAnnotationMutation.mutateAsync({
                taskId: task.id,
                pages: validPages.length || invalidPages.length ? [] : pages,
                userId: task.user_id,
                revision,
                validPages: validPages,
                invalidPages: invalidPages,
                selectedLabelsId: selectedLabels.map(({ id }) => id),
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

    const onCurrentPageChange = (page: number) => {
        setCurrentPage(page);
    };

    const onClearModifiedPages = useCallback(() => {
        setModifiedPages([]);
    }, []);

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

    const taskUserAnnotationsTaxons = useAnnotationsTaxons(latestAnnotationsResult.data?.pages);

    const comparedTaxonLabels: Map<string, Taxon> = useMemo(
        () => new Map([...taskUserAnnotationsTaxons, ...notTaskUserPagesTaxonLabels]),
        [taskUserAnnotationsTaxons, notTaskUserPagesTaxonLabels]
    );
    const { getAnnotationLabels, mapAnnotationPagesFromApi } = useAnnotationsMapper(
        comparedTaxonLabels,
        [latestAnnotationsResult.data?.pages, comparedTaxonLabels]
    );

    const createAnnotation = (
        pageNum: number,
        annData: Annotation,
        category = selectedCategory
    ): Annotation => {
        const pageAnnotations = allAnnotations[pageNum] ?? [];
        const hasTaxonomy = annData.data?.dataAttributes.some(
            ({ type }: CategoryDataAttributeWithValue) => type === 'taxonomy'
        );

        const newAnnotation = {
            ...annData,
            categoryName: category?.name,
            color: category?.metadata?.color,
            label: hasTaxonomy ? annData.label : category?.name,
            labels: getAnnotationLabels(pageNum.toString(), annData, category)
        };

        setAllAnnotations((prevState) => ({
            ...prevState,
            [pageNum]: [...pageAnnotations, newAnnotation]
        }));
        setModifiedPages((prevState) => {
            if (!prevState.includes(pageNum)) return [...prevState, pageNum];
            return prevState;
        });
        setTableMode(newAnnotation.boundType === 'table');
        setSelectedAnnotation(newAnnotation);
        setAnnotationDataAttrs(newAnnotation);
        return newAnnotation;
    };

    const annotationHandlers = useAnnotationHandlers({
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
        annotationsByUserId: notTaskUserAnnotationsByUserId,
        setExternalViewer,
        createAnnotation,
        onAddTouchedPage
    });

    useAnnotationsLinks(
        selectedAnnotation,
        selectedCategory,
        currentPage,
        selectionType,
        allAnnotations,
        annotationHandlers.onAnnotationEdited
    );

    useEffect(() => {
        if (validPages.length && isSplitValidation && job?.status !== JobStatus.Finished) {
            onAnnotationTaskFinish();
        }
    }, [validPages, isSplitValidation]);

    useEffect(() => {
        if (!latestAnnotationsResult.data || !categories) return;
        const {
            categories: latestLabelIds,
            pages,
            pages: [firstPage]
        } = latestAnnotationsResult.data;

        setLatestLabelsId(latestLabelIds);

        const result = mapAnnotationPagesFromApi(
            (page: PageInfo) => page.page_num.toString(),
            pages,
            categories
        );
        setAllAnnotations(result);

        const annDataAttrsResult = mapAnnotationDataAttrsFromApi(
            latestAnnotationsResult.data.pages
        );
        setAnnDataAttrs(annDataAttrsResult);

        if (firstPage?.size?.width && firstPage?.size?.height) {
            setPageSize(firstPage.size);
        }
    }, [latestAnnotationsResult.data, categories, mapAnnotationPagesFromApi]);

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
            setPageSize,
            modifiedPages,
            selectionType,
            selectedTool,
            selectedToolParams,
            setSelectedToolParams,
            onChangeSelectedTool,
            tableMode,
            isNeedToSaveTable,
            setIsNeedToSaveTable,
            tabValue,
            selectedAnnotation,
            isCategoryDataEmpty,
            annDataAttrs,
            externalViewer,
            tableCellCategory,
            setTableCellCategory,
            onLinkDeleted,
            onCategorySelected,
            onChangeSelectionType,
            onSaveTask,
            onAnnotationTaskFinish,
            onCurrentPageChange,
            onClearModifiedPages,
            setTabValue,
            onDataAttributesChange,
            onEmptyAreaClick,
            onExternalViewerClose,
            setSelectedAnnotation,
            selectedLabels,
            onLabelsSelected,
            isDocLabelsModified,
            setSelectedLabels,
            latestLabelsId,
            setCurrentDocumentUserId,
            currentDocumentUserId,
            validPages,
            invalidPages,
            onAddTouchedPage,
            setValidPages,
            categoriesByUserId,
            userPages: notTaskUserPages,
            annotationsByUserId: notTaskUserAnnotationsByUserId,
            ...annotationHandlers,
            ...validationValues,
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
        annotationHandlers,
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
