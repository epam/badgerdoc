import React, {
    createContext,
    ReducerAction,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useReducer,
    useState
} from 'react';
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
    CategoryDataAttribute,
    CategoryDataAttributeWithValue,
    CategoryDataAttrType,
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

const INITIAL_STATE = {
    selectedLabels: [],
    latestLabelsId: [],
    isDocLabelsModified: false,
    allAnnotations: {},
    currentPage: 1,
    modifiedPages: [],
    tabValue: 'Categories',
    selectionType: 'free-box' as AnnotationBoundType,
    selectedTool: ToolNames.pen,
    isCategoryDataEmpty: false,
    annDataAttrs: {},
    externalViewer: defaultExternalViewer,
    tableMode: false,
    tableCellCategory: '',
    isNeedToSaveTable: {
        gutters: undefined,
        cells: undefined
    },
    storedParams: DEFAULT_STORED_PARAMS,
    pageSize: {
        width: DEFAULT_PAGE_WIDTH,
        height: DEFAULT_PAGE_HEIGHT
    }
};

type TState = {
    currentDocumentUserId?: string;
    selectedCategory?: Category;
    selectedLabels: Label[];
    latestLabelsId: string[];
    isDocLabelsModified: boolean;
    allAnnotations: Record<string, Annotation[]>;
    selectedToolParams?: PaperToolParams;
    currentPage: number;
    modifiedPages: number[];
    tabValue: string;
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames;
    selectedTool: ToolNames;
    selectedAnnotation?: Annotation;
    isCategoryDataEmpty: boolean;
    annDataAttrs: Record<string, Array<CategoryDataAttributeWithValue>>;
    externalViewer: ExternalViewerState;
    tableMode: boolean;
    tableCellCategory?: string | number;
    isNeedToSaveTable: {
        gutters: Maybe<TableGutterMap>;
        cells: Maybe<Annotation[]>;
    };
    storedParams: Record<ToolNames, PaperToolParams | undefined>;
    pageSize: { width: number; height: number };
};

const SET_CURRENT_DOCUMENT_USER_ID = 'SET_CURRENT_DOCUMENT_USER_ID';
const SET_SELECTED_CATEGORY = 'SET_SELECTED_CATEGORY';
const SET_SELECTED_LABELS = 'SET_SELECTED_LABELS';
const SET_LATEST_LABELS_ID = 'SET_LATEST_LABELS_ID';
const SET_IS_DOC_LABELS_MODIFIED = 'SET_IS_DOC_LABELS_MODIFIED';
const SET_ALL_ANNOTATIONS = 'SET_ALL_ANNOTATIONS';
const CREATE_ANNOTATION = 'CREATE_ANNOTATION';
const DELETE_ANNOTATION_LINK = 'DELETE_ANNOTATION_LINK';
const UNSELECT_ANNOTATION = 'UNSELECT_ANNOTATION';
const SET_SELECTED_TOOL_PARAMS = 'SET_SELECTED_TOOL_PARAMS';
const SET_CURRENT_PAGE = 'SET_CURRENT_PAGE';
const SET_MODIFIED_PAGES = 'SET_MODIFIED_PAGES';
const SET_TAB_VALUE = 'SET_TAB_VALUE';
const SET_SELECTION_TYPE = 'SET_SELECTION_TYPE';
const SET_SELECTED_TOOL = 'SET_SELECTED_TOOL';
const SET_SELECTED_ANNOTATION = 'SET_SELECTED_ANNOTATION';
const SET_IS_CATEGORY_DATA_EMPTY = 'SET_IS_CATEGORY_DATA_EMPTY';
const SET_ANN_DATA_ATTRS = 'SET_ANN_DATA_ATTRS';
const CHANGE_ANN_DATA_ATTRS = 'CHANGE_ANN_DATA_ATTRS';
const SET_SELECTED_ANN_DATA_ATTRS = 'SET_SELECTED_ANN_DATA_ATTRS';
const SET_EXTERNAL_VIEWER = 'SET_EXTERNAL_VIEWER';
const CLOSE_EXTERNAL_VIEWER = 'CLOSE_EXTERNAL_VIEWER';
const SET_TABLE_MODE = 'SET_TABLE_MODE';
const SET_TABLE_CELL_CATEGORY = 'SET_TABLE_CELL_CATEGORY';
const SET_IS_NEED_TO_SAVE_TABLE = 'SET_IS_NEED_TO_SAVE_TABLE';
const SET_STORED_PARAMS = 'SET_STORED_PARAMS';
const CHANGE_STORED_PARAMS = 'CHANGE_STORED_PARAMS';
const SET_PAGE_SIZE = 'SET_PAGE_SIZE';

type TActionGeneric<T, P = undefined> = {
    type: T;
    payload: P;
};

type TAction =
    | TActionGeneric<typeof SET_CURRENT_DOCUMENT_USER_ID, TState['currentDocumentUserId']>
    | TActionGeneric<typeof SET_SELECTED_CATEGORY, TState['selectedCategory']>
    | TActionGeneric<typeof SET_SELECTED_LABELS, TState['selectedLabels']>
    | TActionGeneric<typeof SET_LATEST_LABELS_ID, TState['latestLabelsId']>
    | TActionGeneric<typeof SET_IS_DOC_LABELS_MODIFIED, TState['isDocLabelsModified']>
    | TActionGeneric<typeof SET_ALL_ANNOTATIONS, TState['allAnnotations']>
    | TActionGeneric<typeof SET_SELECTED_TOOL_PARAMS, TState['selectedToolParams']>
    | TActionGeneric<typeof SET_CURRENT_PAGE, TState['currentPage']>
    | TActionGeneric<typeof SET_MODIFIED_PAGES, TState['modifiedPages']>
    | TActionGeneric<typeof SET_TAB_VALUE, TState['tabValue']>
    | TActionGeneric<typeof SET_SELECTION_TYPE, TState['selectionType']>
    | TActionGeneric<typeof SET_SELECTED_TOOL, TState['selectedTool']>
    | TActionGeneric<typeof SET_SELECTED_ANNOTATION, TState['selectedAnnotation']>
    | TActionGeneric<typeof SET_IS_CATEGORY_DATA_EMPTY, TState['isCategoryDataEmpty']>
    | TActionGeneric<typeof SET_ANN_DATA_ATTRS, TState['annDataAttrs']>
    | TActionGeneric<typeof CHANGE_ANN_DATA_ATTRS, { index: number; value: string }>
    | TActionGeneric<
          typeof SET_SELECTED_ANN_DATA_ATTRS,
          { annotation: Annotation; foundCategoryDataAttrs: CategoryDataAttribute[] }
      >
    | TActionGeneric<typeof SET_EXTERNAL_VIEWER, TState['externalViewer']>
    | TActionGeneric<typeof CLOSE_EXTERNAL_VIEWER>
    | TActionGeneric<typeof SET_TABLE_MODE, TState['tableMode']>
    | TActionGeneric<typeof SET_TABLE_CELL_CATEGORY, TState['tableCellCategory']>
    | TActionGeneric<typeof SET_IS_NEED_TO_SAVE_TABLE, TState['isNeedToSaveTable']>
    | TActionGeneric<typeof SET_STORED_PARAMS, PaperToolParams>
    | TActionGeneric<typeof CHANGE_STORED_PARAMS>
    | TActionGeneric<typeof SET_PAGE_SIZE, TState['pageSize']>
    | TActionGeneric<typeof CREATE_ANNOTATION, { pageNum: number; annotation: Annotation }>
    | TActionGeneric<
          typeof DELETE_ANNOTATION_LINK,
          { pageNum: number; annotationId: Annotation['id']; link: Link }
      >
    | TActionGeneric<typeof UNSELECT_ANNOTATION>;

const reducer = (state: TState, { type, payload }: TAction) => {
    switch (type) {
        case SET_CURRENT_DOCUMENT_USER_ID:
            return { ...state, currentDocumentUserId: payload };
        case SET_SELECTED_CATEGORY:
            return { ...state, selectedCategory: payload };
        case SET_SELECTED_LABELS: {
            const currentLabelsId = payload.map((label) => label.id);
            const isDocLabelsModifiedNewVal =
                state.latestLabelsId.toString() === currentLabelsId.toString();

            return {
                ...state,
                isDocLabelsModifiedNewVal,
                selectedLabels: [...state.selectedLabels, ...payload]
            };
        }
        case UNSELECT_ANNOTATION: {
            return {
                ...state,
                tabValue: 'Categories',
                isCategoryDataEmpty: true,
                selectedAnnotation: undefined
            };
        }
        case SET_LATEST_LABELS_ID:
            return { ...state, latestLabelsId: payload };
        case SET_IS_DOC_LABELS_MODIFIED:
            return { ...state, isDocLabelsModified: payload };
        case SET_ALL_ANNOTATIONS:
            return { ...state, allAnnotations: payload };
        case CREATE_ANNOTATION: {
            const { pageNum, annotation } = payload;
            const pageAnnotations = state.allAnnotations[pageNum] ?? [];

            return {
                ...state,
                selectedAnnotation: annotation,
                annotationDataAttrs: annotation,
                tableMode: annotation.boundType === 'table',
                modifiedPages: state.modifiedPages.includes(pageNum)
                    ? state.modifiedPages
                    : [...state.modifiedPages, pageNum],
                allAnnotations: {
                    ...state.allAnnotations,
                    [pageNum]: [...pageAnnotations, annotation]
                }
            };
        }
        case DELETE_ANNOTATION_LINK: {
            const { pageNum, annotationId, link: linkToDel } = payload;

            const pageAnnotations = (state.allAnnotations[pageNum] ?? []).map((annotation) => {
                if (annotation.id !== annotationId) return annotation;

                return {
                    ...annotation,
                    links: annotation.links?.filter((link) => {
                        return (
                            link.category_id !== linkToDel.category_id &&
                            link.page_num !== linkToDel.page_num &&
                            link.to !== linkToDel.to &&
                            link.type !== linkToDel.type
                        );
                    })
                };
            });

            return {
                ...state,
                allAnnotations: {
                    ...state.allAnnotations,
                    [pageNum]: pageAnnotations
                }
            };
        }
        case SET_SELECTED_TOOL_PARAMS:
            return {
                ...state,
                selectedToolParams: payload
            };
        case SET_CURRENT_PAGE:
            return { ...state, currentPage: payload };
        case SET_MODIFIED_PAGES:
            return { ...state, modifiedPages: payload };
        case SET_TAB_VALUE:
            return { ...state, tabValue: payload };
        case SET_SELECTION_TYPE:
            return { ...state, selectionType: payload };
        case SET_SELECTED_TOOL:
            return { ...state, selectedTool: payload };
        case SET_SELECTED_ANNOTATION:
            return { ...state, selectedAnnotation: payload };
        case SET_IS_CATEGORY_DATA_EMPTY:
            return { ...state, isCategoryDataEmpty: payload };
        case SET_ANN_DATA_ATTRS: {
            return {
                ...state,
                annDataAttrs: payload
            };
        }
        case CHANGE_ANN_DATA_ATTRS: {
            const { index, value } = payload;

            if (!state.selectedAnnotation) return state;

            const dataAttrByAnnotationId = [...state.annDataAttrs[state.selectedAnnotation.id]];
            const dataAttr = dataAttrByAnnotationId[index];

            dataAttrByAnnotationId[index] = { ...dataAttr, value };

            const externalViewer = !isValidCategoryType(dataAttr.type)
                ? state.externalViewer
                : {
                      value,
                      isOpen: true,
                      type: dataAttr.type,
                      name: dataAttr.name
                  };

            return {
                ...state,
                externalViewer,
                annDataAttrs: {
                    ...state.annDataAttrs,
                    [state.selectedAnnotation.id]: dataAttrByAnnotationId
                }
            };
        }
        case SET_SELECTED_ANN_DATA_ATTRS: {
            const { annotation, foundCategoryDataAttrs } = payload;

            if (foundCategoryDataAttrs && foundCategoryDataAttrs.length) {
                return {
                    ...state,
                    tabValue: 'Data',
                    isCategoryDataEmpty: false,
                    selectedAnnotation: annotation,
                    annDataAttrs: {
                        ...state.annDataAttrs,
                        [annotation.id]: mapAnnDataAttrs(
                            foundCategoryDataAttrs,
                            state.annDataAttrs[annotation.id]
                        )
                    }
                };
            }

            return {
                ...state,
                tabValue: 'Categories',
                isCategoryDataEmpty: true
            };
        }
        case SET_EXTERNAL_VIEWER:
            return { ...state, externalViewer: payload };
        case CLOSE_EXTERNAL_VIEWER:
            return { ...state, externalViewer: INITIAL_STATE.externalViewer };
        case SET_TABLE_MODE:
            return { ...state, tableMode: payload };
        case SET_TABLE_CELL_CATEGORY:
            return { ...state, tableCellCategory: payload };
        case SET_IS_NEED_TO_SAVE_TABLE:
            return { ...state, isNeedToSaveTable: payload };
        case SET_STORED_PARAMS:
            return {
                ...state,
                storedParams: {
                    ...state.storedParams,
                    [state.selectedTool]: payload
                }
            };
        case SET_PAGE_SIZE:
            return { ...state, pageSize: payload };
        default:
            return state;
    }
};

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
            pageSize
        },
        dispatch
    ] = useReducer(reducer, INITIAL_STATE);

    // const [currentDocumentUserId, setCurrentDocumentUserId] = useState<string>();
    // const [selectedCategory, setSelectedCategory] = useState<Category>();
    // const [selectedLabels, setSelectedLabels] = useState<Label[]>([]);
    // const [latestLabelsId, setLatestLabelsId] = useState<string[]>([]);
    // const [isDocLabelsModified, setIsDocLabelsModified] = useState<boolean>(false);
    // const [allAnnotations, setAllAnnotations] = useState<Record<string, Annotation[]>>({});
    // const [selectedToolParams, setSelectedToolParams] = useState<PaperToolParams>(
    //     {} as PaperToolParams
    // );

    // const [currentPage, setCurrentPage] = useState<number>(1);

    // const [modifiedPages, setModifiedPages] = useState<number[]>([]);
    // const [tabValue, setTabValue] = useState<string>('Categories');
    // const [selectionType, setSelectionType] = useState<
    //     AnnotationBoundType | AnnotationLinksBoundType | ToolNames
    // >('free-box');
    // const [selectedTool, setSelectedTool] = useState<ToolNames>(ToolNames.pen);
    // const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | undefined>();
    // const [isCategoryDataEmpty, setIsCategoryDataEmpty] = useState<boolean>(false);
    // const [annDataAttrs, setAnnDataAttrs] = useState<
    //     Record<string, Array<CategoryDataAttributeWithValue>>
    // >({});
    // const [externalViewer, setExternalViewer] =
    //     useState<ExternalViewerState>(defaultExternalViewer);

    // const [tableMode, setTableMode] = useState<boolean>(false);
    // const [tableCellCategory, setTableCellCategory] = useState<string | number | undefined>('');

    // const [isNeedToSaveTable, setIsNeedToSaveTable] = useState<{
    //     gutters: Maybe<TableGutterMap>;
    //     cells: Maybe<Annotation[]>;
    // }>({
    //     gutters: undefined,
    //     cells: undefined
    // });

    // const [storedParams, setStoredParams] =
    //     useState<Record<ToolNames, PaperToolParams | undefined>>(DEFAULT_STORED_PARAMS);

    // const [pageSize, setPageSize] = useState<{ width: number; height: number }>({
    //     width: DEFAULT_PAGE_WIDTH,
    //     height: DEFAULT_PAGE_HEIGHT
    // });

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
            dispatch({ type: SET_CURRENT_PAGE, payload: pageNumbers[0] });
            documentsResult.refetch();
            latestAnnotationsResult.refetch();
            refetchTokens();
        }
    }, [task, job, revisionId]);

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

    useEffect(() => {
        if (!selectedAnnotation) return;

        setAnnotationDataAttrs(selectedAnnotation);
    }, [selectedAnnotation]);

    const onCloseDataTab = () => {
        dispatch({ type: SET_TAB_VALUE, payload: 'Categories' });
        onExternalViewerClose();
    };

    const onLabelsSelected = (labels: Label[]) => {
        if (!Array.isArray(labels)) return;

        dispatch({ type: SET_SELECTED_LABELS, payload: labels });
    };

    const onChangeSelectionType = (
        newType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames
    ) => {
        dispatch({ type: SET_SELECTION_TYPE, payload: newType });
    };

    const onChangeSelectedTool = (newTool: ToolNames) => {
        dispatch({ type: SET_SELECTED_TOOL, payload: newTool });
        onChangeSelectionType('polygon');
    };

    const onExternalViewerClose = () => {
        dispatch({ type: CLOSE_EXTERNAL_VIEWER, payload: undefined });
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

    const onDataAttributesChange = (index: number, value: string) => {
        dispatch({ type: CHANGE_ANN_DATA_ATTRS, payload: { index, value } });
    };

    const onLinkDeleted = (pageNum: number, annotationId: string | number, linkToDel: Link) => {
        dispatch({
            type: DELETE_ANNOTATION_LINK,
            payload: { pageNum, annotationId, link: linkToDel }
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

    const annotationHandlers = useAnnotationHandlers({
        allAnnotations,
        setAllAnnotations: (payload: Record<string, Annotation[]>) =>
            dispatch({ type: SET_ALL_ANNOTATIONS, payload }),
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

        dispatch({ type: SET_LATEST_LABELS_ID, payload: latestLabelIds });

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
            onChangeSelectionType,
            onSaveTask,
            onAnnotationTaskFinish,
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
            onClearModifiedPages: () => dispatch({ type: SET_MODIFIED_PAGES, payload: [] }),
            onCurrentPageChange: (currentPage: number) =>
                dispatch({ type: SET_CURRENT_PAGE, payload: currentPage }),
            setCurrentDocumentUserId: (documentId: string) =>
                dispatch({ type: SET_CURRENT_DOCUMENT_USER_ID, payload: documentId }),
            onCategorySelected: (category: Category) => {
                dispatch({ type: SET_SELECTED_CATEGORY, payload: category });
            },
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
