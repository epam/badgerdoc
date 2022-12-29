import { ApiError } from 'api/api-error';
import { useAddAnnotationsMutation, useLatestAnnotations } from 'api/hooks/annotations';
import { useCurrentUser } from 'api/hooks/auth';
import { useCategoriesByJob } from 'api/hooks/categories';
import { useDocuments } from 'api/hooks/documents';
import { useJobById } from 'api/hooks/jobs';
import { useSetTaskFinished, useSetTaskState, useTaskById } from 'api/hooks/tasks';
import { useTokens } from 'api/hooks/tokens';
import {
    Category,
    CategoryDataAttributeWithValue,
    ExternalViewerState,
    FileDocument,
    Filter,
    Link,
    Operators,
    PageInfo,
    SortingDirection,
    User
} from 'api/typings';
import { Job } from 'api/typings/jobs';
import { Task } from 'api/typings/tasks';
import { cloneDeep } from 'lodash';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import React, {
    createContext,
    MutableRefObject,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState
} from 'react';
import { QueryObserverResult, RefetchOptions, RefetchQueryFilters } from 'react-query';
import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType,
    Maybe,
    PageToken,
    PaperToolParams,
    TableGutterMap,
    toolNames
} from 'shared';
import { useAnnotationsLinks } from 'shared/components/annotator/utils/use-annotation-links';
import { documentSearchResultMapper } from 'shared/helpers/document-search-result-mapper';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import useSycnScroll, { SyncScrollValue } from 'shared/hooks/use-sync-scroll';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import {
    defaultExternalViewer,
    getCategoryDataAttrs,
    isValidCategoryType,
    mapAnnDataAttrs,
    mapAnnotationDataAttrsFromApi,
    mapModifiedAnnotationPagesToApi,
    mapTokenPagesFromApi
} from './task-annotator-utils';
import useSplitValidation, { SplitValidationValue } from './use-split-validation';
import { useUsersDataFromTask } from './user-fetch-hook';

type ContextValue = SplitValidationValue &
    SyncScrollValue & {
        task?: Task;
        job?: Job;
        categories?: Category[];
        categoriesLoading?: boolean;
        selectedCategory?: Category;
        selectedLink?: Link;
        selectedAnnotation?: Annotation;
        fileMetaInfo: FileMetaInfo;
        tokensByPages: Record<number, PageToken[]>;
        allAnnotations?: Record<number, Annotation[]>;
        pageNumbers: number[];
        currentPage: number;
        validPages: number[];
        invalidPages: number[];
        editedPages: number[];
        touchedPages: number[];
        modifiedPages: number[];
        pageSize?: { width: number; height: number };
        setPageSize: (pS: any) => void;
        tabValue: string;
        isOwner: boolean;
        sortedUsers: MutableRefObject<{ owners: User[]; annotators: User[]; validators: User[] }>;
        selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType;
        selectedTool: AnnotationImageToolType;
        setSelectedTool: (t: AnnotationImageToolType) => void;
        onChangeSelectedTool: (t: AnnotationImageToolType) => void;
        tableMode: boolean;
        isNeedToSaveTable: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        };
        setIsNeedToSaveTable: (b: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        }) => void;
        isDataTabDisabled: boolean;
        isCategoryDataEmpty: boolean;
        annDataAttrs: Record<number, Array<CategoryDataAttributeWithValue>>;
        externalViewer: ExternalViewerState;
        onChangeSelectionType: (
            newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
        ) => void;
        onCategorySelected: (category: Category) => void;
        onLinkSelected: (link: Link) => void;
        onSaveTask: () => void;
        onExternalViewerClose: () => void;
        onAnnotationTaskFinish: () => void;
        onAnnotationCreated: (pageNum: number, annotation: Annotation) => void;
        onAnnotationDeleted: (pageNum: number, annotationId: string | number) => void;
        onAnnotationEdited: (
            pageNum: number,
            annotationId: string | number,
            changes: Partial<Annotation>
        ) => void;
        onLinkDeleted: (pageNum: number, annotationId: string | number, link: Link) => void;
        onCurrentPageChange: (page: number) => void;
        onValidClick: () => void;
        onInvalidClick: () => void;
        onEditClick: () => void;
        onCancelClick: () => void;
        onClearTouchedPages: () => void;
        onClearModifiedPages: () => void;
        onAddTouchedPage: () => void;
        onSaveEditClick: () => void;
        onEmptyAreaClick: () => void;
        onAnnotationDoubleClick: (annotation: Annotation) => void;
        onAnnotationCopyPress: (pageNum: number, annotationId: string | number) => void;
        onAnnotationCutPress: (pageNum: number, annotationId: string | number) => void;
        onAnnotationPastePress: (pageSize: PageSize, pageNum: number) => void;
        onAnnotationUndoPress: () => void;
        onAnnotationRedoPress: () => void;
        setTabValue: (value: string) => void;
        onDataAttributesChange: (elIndex: number, value: string) => void;
        tableCellCategory: string | number | undefined;
        setTableCellCategory: (s: string | number | undefined) => void;
        selectedToolParams: PaperToolParams;
        setSelectedToolParams: (nt: PaperToolParams) => void;
        setSelectedAnnotation: (annotation: Annotation | undefined) => void;
        taskHasTaxonomies?: boolean;
        setValidPages: (pages: number[]) => void;
    };

const TaskAnnotatorContext = createContext<ContextValue | undefined>(undefined);

type ProviderProps = {
    taskId?: number;
    fileMetaInfo?: FileMetaInfo;
    jobId?: number;
    revisionId?: string;
    onRedirectAfterFinish: () => void;
    onSaveTaskSuccess: () => void;
    onSaveTaskError: (error: ApiError) => void;
};

type UndoListAction = 'edit' | 'delete' | 'add';

const dataTabDefaultDisableState = true;

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
    const [selectedCategory, setSelectedCategory] = useState<Category>();
    const [selectedLink, setSelectedLink] = useState<Link>();
    const [allAnnotations, setAllAnnotations] = useState<Record<number, Annotation[]>>({});

    const [copiedAnnotation, setCopiedAnnotation] = useState<Annotation>();
    const copiedAnnotationReference = useRef<Annotation | undefined>();
    copiedAnnotationReference.current = copiedAnnotation;

    const [undoList, setUndoList] = useState<
        { action: UndoListAction; annotation: Annotation; pageNumber: number }[]
    >([]);
    const [undoPointer, setUndoPointer] = useState<number>(-1);

    const [selectedToolParams, setSelectedToolParams] = useState<PaperToolParams>(
        {} as PaperToolParams
    );

    const [currentPage, setCurrentPage] = useState<number>(1);
    const [validPages, setValidPages] = useState<number[]>([]);
    const [invalidPages, setInvalidPages] = useState<number[]>([]);
    const [editedPages, setEditedPages] = useState<number[]>([]);
    const [touchedPages, setTouchedPages] = useState<number[]>([]);
    const [modifiedPages, setModifiedPages] = useState<number[]>([]);
    const [tabValue, setTabValue] = useState<string>('Categories');
    const [selectionType, setSelectionType] = useState<
        AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
    >('free-box');
    const [selectedTool, setSelectedTool] = useState<AnnotationImageToolType>('pen');
    const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | undefined>(undefined);
    const [isDataTabDisabled, setIsDataTabDisabled] = useState<boolean>(dataTabDefaultDisableState);
    const [isCategoryDataEmpty, setIsCategoryDataEmpty] = useState<boolean>(false);
    const [annDataAttrs, setAnnDataAttrs] = useState<
        Record<number, Array<CategoryDataAttributeWithValue>>
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

    const [storedParams, setStoredParams] = useState<{
        [k in typeof toolNames[number]]: Maybe<PaperToolParams>;
    }>({
        brush: undefined,
        dextr: undefined,
        eraser: undefined,
        pen: undefined,
        rectangle: undefined,
        select: undefined,
        wand: undefined
    });

    const defaultPageWidth: number = 0;
    const defaultPageHeight: number = 0;
    let fileMetaInfo: FileMetaInfo = fileMetaInfoParam!;

    const [pageSize, setPageSize] = useState<{ width: number; height: number }>({
        width: defaultPageWidth,
        height: defaultPageHeight
    });

    let task: Task | undefined;
    let isTaskLoading: boolean = false;
    let refetchTask: (
        options?: (RefetchOptions & RefetchQueryFilters<Task>) | undefined
    ) => Promise<QueryObserverResult<Task, unknown>>;
    if (taskId) {
        const result = useTaskById({ taskId }, {});
        task = result.data;
        isTaskLoading = result.isLoading;
        refetchTask = result.refetch;
    }

    const getJobId = (): number | undefined => (task ? task.job.id : jobId);

    const getFileId = (): number | undefined => (task ? task.file.id : fileMetaInfo?.id);

    const { isOwner, sortedUsers } = useUsersDataFromTask(task);

    const { data: job } = useJobById({ jobId: task?.job.id });

    let pageNumbers: number[] = [];

    if (task) {
        pageNumbers = task.pages;
    } else if (fileMetaInfo?.pages) {
        for (let i = 0; i < fileMetaInfo.pages; i++) {
            pageNumbers.push(i + 1);
        }
    }

    const {
        data: categories,
        refetch: refetchCategories,
        isLoading: categoriesLoading
    } = useCategoriesByJob(
        {
            jobId: getJobId(),
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );

    useEffect(() => {
        if (task?.job.id) {
            refetchCategories();
        }
    }, [task]);

    const taskHasTaxonomies = useMemo(() => {
        if (categories) {
            return !!categories.data.find((category) =>
                category.data_attributes?.find((attr) => attr.type === 'taxonomy')
            );
        }
    }, [categories]);

    const documentFilters: Filter<keyof FileDocument>[] = [];

    documentFilters.push({
        field: 'id',
        operator: Operators.EQ,
        value: getFileId()
    });
    const documentsResult = useDocuments(
        {
            filters: documentFilters
        },
        { enabled: false }
    );
    const latestAnnotationsResult = useLatestAnnotations(
        {
            jobId: getJobId(),
            fileId: getFileId(),
            revisionId,
            pageNumbers: pageNumbers,
            userId: job?.validation_type === 'extensive_coverage' ? task?.user_id : ''
        },
        { enabled: !!(task || job) }
    );

    const tokenRes = useTokens(
        {
            fileId: getFileId(),
            pageNumbers: pageNumbers
        },
        { enabled: false }
    );
    const tokenPages = tokenRes.data;

    if (!fileMetaInfo) {
        fileMetaInfo = useMemo(
            () => ({
                ...documentSearchResultMapper(documentsResult.data),
                isLoading: isTaskLoading || documentsResult.isLoading
            }),
            [documentsResult.data, documentsResult.isLoading, isTaskLoading]
        );
    }

    useEffect(() => {
        if (task || job) {
            setCurrentPage(pageNumbers[0]);
            documentsResult.refetch();
            latestAnnotationsResult.refetch();
            tokenRes.refetch();
        }
    }, [task, job]);

    const { getAnnotationLabels, mapAnnotationPagesFromApi } = useAnnotationsMapper([
        latestAnnotationsResult.data
    ]);

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
        category: Category | undefined = selectedCategory
    ): Annotation => {
        const pageAnnotations = allAnnotations[pageNum] ?? [];
        const dataAttr: CategoryDataAttributeWithValue = annData.data?.dataAttributes.find(
            (attr: CategoryDataAttributeWithValue) => attr.type === 'taxonomy'
        );
        const newAnnotation = {
            ...annData,
            color: category?.metadata?.color,
            label: dataAttr ? dataAttr.value : category?.name,
            labels: getAnnotationLabels(pageNum.toString(), annData, category)
        };
        setAllAnnotations((prevState) => ({
            ...prevState,
            [pageNum]: [...pageAnnotations, newAnnotation]
        }));

        setModifiedPages((prevState) => {
            return Array.from(new Set([...prevState, pageNum]));
        });
        setTableMode(newAnnotation.boundType === 'table');
        setSelectedAnnotation(newAnnotation);
        setIsDataTabDisabled(false);
        setAnnotationDataAttrs(newAnnotation);
        return newAnnotation;
    };

    const onAnnotationCreated = (pageNum: number, annData: Annotation, category?: Category) => {
        const newAnnotation = createAnnotation(pageNum, annData, category);

        updateUndoList(pageNum, cloneDeep(annData), 'add');
        return newAnnotation;
    };

    const deleteAnnotation = (pageNum: number, annotationId: string | number) => {
        const pageAnnotations = allAnnotations[pageNum] ?? [];
        const anntn: Maybe<Annotation> = pageAnnotations.find((el) => el.id === annotationId);
        if (anntn?.labels) {
            const labelIdxToDelete = anntn.labels.findIndex(
                (item) => item.annotationId === annotationId
            );
            if (labelIdxToDelete !== -1) {
                anntn?.labels?.splice(labelIdxToDelete, 1);
            }
        }
        setAllAnnotations((prevState) => {
            for (let k in prevState) {
                prevState[k].map((annList) =>
                    annList?.links?.filter((link) => link.to !== annotationId)
                );
            }
            return {
                ...prevState,
                [pageNum]: pageAnnotations.filter((ann) => {
                    if (
                        anntn &&
                        anntn.children &&
                        anntn.boundType === 'table' &&
                        (anntn.children as number[]).includes(+ann.id) &&
                        ann.boundType === 'table_cell'
                    ) {
                        return false;
                    }
                    return ann.id !== annotationId;
                })
            };
        });

        setModifiedPages((prevState) => {
            return Array.from(new Set([...prevState, pageNum]));
        });
    };

    const onAnnotationDeleted = (pageNum: number, annotationId: string | number) => {
        const annotationBeforeModification = allAnnotations[pageNum]?.find(
            (item) => item.id === annotationId
        );
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'delete');

        deleteAnnotation(pageNum, annotationId);
    };

    const onCategorySelected = (category: Category) => {
        setSelectedCategory(category);
    };

    const onLinkSelected = (link: Link) => {
        setSelectedLink(link);
    };

    const onChangeSelectionType = (
        newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
    ) => {
        setSelectionType(newType);
    };

    const onChangeSelectedTool = (newTool: AnnotationImageToolType) => {
        setSelectedTool(newTool);
        setSelectionType('polygon');
    };

    useEffect(() => {
        setStoredParams({
            ...storedParams,
            [selectedTool]: selectedToolParams
        });
    }, [selectedToolParams]);

    useEffect(() => {
        switch (selectedTool) {
            case 'eraser':
                if (storedParams.eraser) setSelectedToolParams(storedParams.eraser);
                else
                    setSelectedToolParams({
                        type: 'slider-number',
                        values: {
                            radius: { value: 40, bounds: { min: 0, max: 150 } }
                        }
                    });
                break;
            case 'brush':
                if (storedParams.brush) setSelectedToolParams(storedParams.brush);
                else
                    setSelectedToolParams({
                        type: 'slider-number',
                        values: {
                            radius: { value: 40, bounds: { min: 0, max: 150 } }
                        }
                    });
                break;
            case 'wand':
                if (storedParams.wand) setSelectedToolParams(storedParams.wand);
                else
                    setSelectedToolParams({
                        type: 'slider-number',
                        values: {
                            threshold: { value: 35, bounds: { min: 0, max: 150 } },
                            deviation: { value: 15, bounds: { min: 0, max: 150 } }
                        }
                    });
                break;
            case 'dextr':
            case 'rectangle':
            case 'select':
            case 'pen':
                break;
        }
    }, [selectedTool]);

    const onExternalViewerClose = () => setExternalViewer(defaultExternalViewer);

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

    const onEmptyAreaClick = () => {
        setIsDataTabDisabled(dataTabDefaultDisableState);
        setAnnDataAttrs({});
        setIsCategoryDataEmpty(true);
        setTabValue('Categories');
        setSelectedAnnotation(undefined);
    };

    const setAnnotationDataAttrs = (annotation: Annotation) => {
        const foundCategoryDataAttrs = getCategoryDataAttrs(
            annotation.category ? annotation.category : annotation.label,
            categories?.data
        );
        if (foundCategoryDataAttrs && foundCategoryDataAttrs.length) {
            setAnnDataAttrs((prevState) => {
                prevState[+annotation.id] = mapAnnDataAttrs(
                    foundCategoryDataAttrs,
                    prevState[+annotation.id]
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
        setIsDataTabDisabled(foundCategoryDataAttrs && foundCategoryDataAttrs.length === 0);
    };

    useEffect(() => {
        if (!selectedAnnotation) return;

        setAnnotationDataAttrs(selectedAnnotation);
    }, [selectedAnnotation]);

    const onAnnotationCopyPress = (pageNum: number, annotationId: string | number) => {
        if (annotationId && pageNum) {
            const annotation = allAnnotations[pageNum].find((item) => item.id === annotationId);
            if (annotation) {
                setCopiedAnnotation(annotation);
            }
        }
    };

    const onAnnotationCutPress = (pageNum: number, annotationId: string | number) => {
        onAnnotationCopyPress(pageNum, annotationId);
        onAnnotationDeleted(pageNum, annotationId);
    };

    const onAnnotationPastePress = (pageSize: PageSize, pageNum: number) => {
        const annotationToPaste = copiedAnnotationReference.current;
        if (!annotationToPaste) {
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

    // swap annotation state and its saved state in undoList
    const swapAnnotationState = (
        pageNumber: number,
        annotationId: number | string,
        undoPointer: number
    ) => {
        const oldAnnotationState = cloneDeep(
            allAnnotations[pageNumber].find((item) => item.id === annotationId)
        );

        modifyAnnotation(pageNumber, annotationId, undoList[undoPointer].annotation);

        const undoListCopy = cloneDeep(undoList);
        undoListCopy[undoPointer].annotation = oldAnnotationState!;
        setUndoList(undoListCopy);
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

    const onAnnotationDoubleClick = (annotation: Annotation) => {
        const { id, label } = annotation;

        if (annotation.boundType === 'table') {
            setTableMode(true);
            setTabValue('Data');
            setSelectedAnnotation(annotation);
            return;
        } else {
            setTableMode(false);
        }

        const foundCategoryDataAttrs = getCategoryDataAttrs(label, categories?.data);

        if (foundCategoryDataAttrs) {
            setAnnDataAttrs((prevState) => {
                const mapAttributes = mapAnnDataAttrs(foundCategoryDataAttrs, prevState[+id]);

                findAndSetExternalViewerType(mapAttributes);
                prevState[+id] = mapAttributes;

                return prevState;
            });
            setIsCategoryDataEmpty(false);
            setSelectedAnnotation(annotation);
        } else {
            setIsCategoryDataEmpty(true);
            setSelectedAnnotation(undefined);
        }
    };

    const onDataAttributesChange = (elIndex: number, value: string) => {
        const newAnn = { ...annDataAttrs };

        if (selectedAnnotation) {
            const annItem = newAnn[+selectedAnnotation.id][elIndex];
            newAnn[+selectedAnnotation.id][elIndex].value = value;

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

    const addAnnotationMutation = useAddAnnotationsMutation();

    const modifyAnnotation = (
        pageNum: number,
        id: string | number,
        changes: Partial<Annotation>
    ) => {
        setAllAnnotations((prevState) => {
            if (pageNum === -1) {
                pageNum = (Object.keys(prevState) as unknown as Array<number>).find((key: number) =>
                    prevState[key].find((ann) => ann.id == id)
                )!;
            }
            const pageAnnotations = prevState[pageNum] ?? [];
            return {
                ...prevState,
                [pageNum]: pageAnnotations.map((ann) => {
                    if (ann.id === id) {
                        return { ...ann, ...changes, id };
                    }
                    return ann;
                })
            };
        });
        setModifiedPages((prevState) => {
            return Array.from(new Set([...prevState, pageNum]));
        });
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

    const onAnnotationEdited = (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => {
        const annotationBeforeModification = allAnnotations[pageNum]?.find(
            (item) => item.id === annotationId
        );
        updateUndoList(pageNum, cloneDeep(annotationBeforeModification), 'edit');
        modifyAnnotation(pageNum, annotationId, changes);
    };
    const onCloseDataTab = () => {
        setTabValue('Categories');
        setIsDataTabDisabled(true);
        onExternalViewerClose();
    };
    const onSaveTask = async () => {
        if (!task || !latestAnnotationsResult.data) return;

        let { revision, pages } = latestAnnotationsResult.data;

        onCloseDataTab();

        if (task.is_validation && !splitValidation.isSplitValidation) {
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
                pages,
                userId: task.user_id,
                revision,
                validPages,
                invalidPages
            });
            onSaveTaskSuccess();
            latestAnnotationsResult.refetch();
            refetchTask();
        } catch (error) {
            onSaveTaskError(error as ApiError);
        }
    };

    const onAnnotationTaskFinish = () => {
        if (task) {
            onSaveTask().then((e) => {
                useSetTaskFinished(task!.id);
                useSetTaskState({ id: task!.id, eventType: 'closed' });
                onRedirectAfterFinish();
            });
        }
    };

    const onCurrentPageChange = (page: number) => {
        setCurrentPage(page);
    };

    useEffect(() => {
        if (!latestAnnotationsResult.data || !categories?.data) return;
        setValidPages(latestAnnotationsResult.data.validated);
        setInvalidPages(latestAnnotationsResult.data.failed_validation_pages);

        const result = mapAnnotationPagesFromApi(
            (page: PageInfo) => page.page_num.toString(),
            latestAnnotationsResult.data.pages,
            categories?.data
        );
        setAllAnnotations(result);

        const annDataAttrsResult = mapAnnotationDataAttrsFromApi(
            latestAnnotationsResult.data.pages
        );
        setAnnDataAttrs(annDataAttrsResult);

        if (
            latestAnnotationsResult.data.pages.length === 0 ||
            !latestAnnotationsResult.data.pages[0].size ||
            latestAnnotationsResult.data.pages[0].size.width === 0 ||
            latestAnnotationsResult.data.pages[0].size.height === 0
        )
            return;
        setPageSize(latestAnnotationsResult.data.pages[0].size);
    }, [latestAnnotationsResult.data, categories?.data]);

    const onValidClick = useCallback(() => {
        if (invalidPages.includes(currentPage)) {
            const newInvalidPages = invalidPages.filter((page) => page !== currentPage);
            setInvalidPages(newInvalidPages);
        }
        setValidPages([...validPages, currentPage]);
    }, [invalidPages, validPages, currentPage]);

    const onInvalidClick = useCallback(() => {
        if (validPages.includes(currentPage)) {
            const newValidPages = validPages.filter((page) => page !== currentPage);
            setValidPages(newValidPages);
        }
        setInvalidPages([...invalidPages, currentPage]);
    }, [invalidPages, validPages, currentPage]);

    const onClearTouchedPages = useCallback(async () => {
        setTouchedPages([]);
    }, []);

    const onClearModifiedPages = useCallback(async () => {
        setModifiedPages([]);
    }, []);

    const onAddTouchedPage = useCallback(() => {
        !touchedPages.includes(currentPage)
            ? setTouchedPages([...touchedPages, currentPage])
            : () => {};
    }, [touchedPages, currentPage]);

    const onEditClick = useCallback(() => {
        setEditedPages([...editedPages, currentPage]);
        if (invalidPages.includes(currentPage)) {
            const newInvalidPages = invalidPages.filter((page) => page !== currentPage);
            setInvalidPages(newInvalidPages);
        }
    }, [editedPages, invalidPages, currentPage]);

    const onCancelClick = useCallback(() => {
        onCloseDataTab();

        if (editedPages.includes(currentPage)) {
            const newEditedPages = editedPages.filter((page) => page !== currentPage);
            setEditedPages(newEditedPages);
        }
        setInvalidPages([...invalidPages, currentPage]);
    }, [editedPages, invalidPages, currentPage]);

    const onSaveEditClick = useCallback(async () => {
        if (!task || !latestAnnotationsResult.data || !tokenPages) return;

        let { revision } = latestAnnotationsResult.data;
        const pages = mapModifiedAnnotationPagesToApi(
            editedPages,
            allAnnotations,
            tokensByPages,
            tokenPages,
            annDataAttrs,
            pageSize
        );

        onCloseDataTab();

        if (!taskId) {
            return;
        }

        try {
            await addAnnotationMutation.mutateAsync({
                taskId,
                pages,
                userId: task.user_id,
                revision,
                validPages,
                invalidPages
            });
            onCancelClick();
            onSaveTaskSuccess();

            latestAnnotationsResult.refetch();
        } catch (error) {
            onSaveTaskError(error as ApiError);
        }
    }, [allAnnotations, editedPages, currentPage]);

    const tokensByPages = useMemo<Record<number, PageToken[]>>(() => {
        if (!tokenPages?.length) {
            return {};
        }
        const tokenScale =
            pageSize && tokenPages[0].size && tokenPages[0].size.width
                ? pageSize.width / tokenPages[0].size?.width!
                : 1;
        return mapTokenPagesFromApi(tokenPages, tokenScale);
    }, [tokenPages, pageSize]);

    const syncScroll = useSycnScroll();

    const splitValidation = useSplitValidation({
        categories: categories?.data,
        currentPage,
        fileId: getFileId(),
        isValidation: task?.is_validation,
        job,
        validatorAnnotations: allAnnotations,
        onAnnotationCreated,
        onAnnotationEdited,
        onAddTouchedPage,
        setSelectedAnnotation,
        setValidPages,
        userId: task?.user_id
    });

    const value = useMemo<ContextValue>(() => {
        return {
            task,
            job,
            categories: categories?.data,
            categoriesLoading,
            selectedCategory,
            selectedLink,
            fileMetaInfo,
            tokensByPages,
            allAnnotations,
            pageNumbers,
            currentPage,
            validPages,
            invalidPages,
            pageSize,
            setPageSize,
            editedPages,
            touchedPages,
            modifiedPages,
            selectionType,
            selectedTool,
            setSelectedTool,
            selectedToolParams,
            setSelectedToolParams,
            onChangeSelectedTool,
            tableMode,
            isNeedToSaveTable,
            setIsNeedToSaveTable,
            tabValue,
            selectedAnnotation,
            sortedUsers,
            isOwner,
            isDataTabDisabled,
            isCategoryDataEmpty,
            annDataAttrs,
            externalViewer,
            tableCellCategory,
            taskHasTaxonomies,
            setTableCellCategory,
            onAnnotationCreated,
            onAnnotationDeleted,
            onAnnotationEdited,
            onLinkDeleted,
            onCategorySelected,
            onLinkSelected,
            onChangeSelectionType,
            onSaveTask,
            onAnnotationTaskFinish,
            onCurrentPageChange,
            onValidClick,
            onInvalidClick,
            onEditClick,
            onAddTouchedPage,
            onClearTouchedPages,
            onClearModifiedPages,
            onCancelClick,
            onSaveEditClick,
            setTabValue,
            onDataAttributesChange,
            onEmptyAreaClick,
            onAnnotationDoubleClick,
            onAnnotationCopyPress,
            onAnnotationCutPress,
            onAnnotationPastePress,
            onAnnotationUndoPress,
            onAnnotationRedoPress,
            onExternalViewerClose,
            setSelectedAnnotation,
            setValidPages,
            ...splitValidation,
            ...syncScroll
        };
    }, [
        task,
        categories?.data,
        categoriesLoading,
        selectedCategory,
        selectedLink,
        selectionType,
        selectedTool,
        fileMetaInfo,
        tokensByPages,
        allAnnotations,
        currentPage,
        validPages,
        invalidPages,
        touchedPages,
        pageSize,
        tableMode,
        isNeedToSaveTable,
        tabValue,
        selectedAnnotation,
        annDataAttrs,
        externalViewer,
        tableCellCategory,
        isDataTabDisabled,
        selectedToolParams,
        splitValidation,
        syncScroll
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
