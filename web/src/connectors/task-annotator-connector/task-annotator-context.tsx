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
import { cloneDeep, isEqual } from 'lodash';
import { Task } from 'api/typings/tasks';
import { ApiError } from 'api/api-error';
import {
    DocumentLink,
    useAddAnnotationsMutation,
    useLatestAnnotations
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
    FileDocument,
    FilterWithDocumentExtraOption,
    Label,
    Link,
    Operators,
    PageInfo,
    SortingDirection,
    Taxon,
    User
} from 'api/typings';
import { Job } from 'api/typings/jobs';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';

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
import useAnnotationsTaxons from 'shared/hooks/use-annotations-taxons';
import useAnnotationsMapper from 'shared/hooks/use-annotations-mapper';
import useSyncScroll, { SyncScrollValue } from 'shared/hooks/use-sync-scroll';
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
import { DocumentLinksValue, useDocumentLinks } from './use-document-links';
import { useValidation, ValidationValues } from './use-validation';

type ContextValue = SplitValidationValue &
    SyncScrollValue &
    DocumentLinksValue &
    ValidationValues & {
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
        onClearModifiedPages: () => void;
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
        selectedLabels?: Label[];
        onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
        setSelectedLabels: (labels: Label[]) => void;
        latestLabelsId: string[];
        isDocLabelsModified: boolean;
        getJobId: () => number | undefined;
        linksFromApi?: DocumentLink[];
    };

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

const TaskAnnotatorContext = createContext<ContextValue | undefined>(undefined);
const dataTabDefaultDisableState = true;
const defaultPageWidth: number = 0;
const defaultPageHeight: number = 0;

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
    const [selectedLabels, setSelectedLabels] = useState<Label[]>([]);
    const [latestLabelsId, setLatestLabelsId] = useState<string[]>([]);
    const [isDocLabelsModified, setIsDocLabelsModified] = useState<boolean>(false);
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
        data: { pages: categories } = {},
        refetch: refetchCategories,
        isLoading: categoriesLoading
    } = useCategoriesByJob(
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

    const taskHasTaxonomies = useMemo(() => {
        if (categories) {
            return !!categories.find((category) =>
                category.data_attributes?.find((attr) => attr.type === 'taxonomy')
            );
        }
    }, [categories]);

    const documentFilters: FilterWithDocumentExtraOption<keyof FileDocument>[] = [];

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
            userId:
                job?.validation_type === 'extensive_coverage' && !revisionId ? task?.user_id : ''
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
        if (task || job || revisionId) {
            setCurrentPage(pageNumbers[0]);
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
        category: Category | undefined = selectedCategory
    ): Annotation => {
        const pageAnnotations = allAnnotations[pageNum] ?? [];
        const hasTaxonomy = !!annData.data?.dataAttributes.find(
            (attr: CategoryDataAttributeWithValue) => attr.type === 'taxonomy'
        );

        const newAnnotation = {
            ...annData,
            color: category?.metadata?.color,
            label: hasTaxonomy ? annData.label : category?.name,
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
    const onCloseDataTab = () => {
        setTabValue('Categories');
        setIsDataTabDisabled(true);
        onExternalViewerClose();
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

    const onLabelsSelected = (labels: Label[], pickedLabels: string[]) => {
        if (!Array.isArray(labels)) return;

        const currentLabelsId = labels.map((label) => label.id);
        const isDocLabelsModifiedNewVal = !isEqual(latestLabelsId, currentLabelsId);

        setIsDocLabelsModified(isDocLabelsModifiedNewVal);

        setSelectedLabels((prev) => {
            const combinedLabels = [...prev, ...labels];
            const arrayUniqueByKey = [
                ...new Map(combinedLabels.map((item) => [item['id'], item])).values()
            ].filter((label) => pickedLabels.includes(label.id));
            return arrayUniqueByKey;
        });
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

    const onSaveTask = async () => {
        if (!task || !latestAnnotationsResult.data) return;

        let { revision, pages } = latestAnnotationsResult.data;

        const selectedLabelsId: string[] = selectedLabels.map((obj) => obj.id) ?? [];

        onCloseDataTab();

        if (task.is_validation && !splitValidation.isSplitValidation) {
            validationValues.setAnnotationSaved(true);
            pages = pages.filter(
                (page) =>
                    validationValues.validPages.includes(page.page_num) ||
                    validationValues.invalidPages.includes(page.page_num)
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
                pages:
                    validationValues.validPages.length || validationValues.invalidPages.length
                        ? []
                        : pages,
                userId: task.user_id,
                revision,
                validPages: validationValues.validPages,
                invalidPages: validationValues.invalidPages,
                selectedLabelsId,
                links: documentLinksValues.linksToApi
            });
            onSaveTaskSuccess();
            latestAnnotationsResult.refetch();
            refetchTask();
            documentLinksValues?.setDocumentLinksChanged?.(false);
        } catch (error) {
            onSaveTaskError(error as ApiError);
        }
    };
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

    const validationValues = useValidation({
        latestAnnotationsResult,
        task,
        currentPage,
        sortedUsers,
        isOwner,
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
                await finishTaskMutation.mutateAsync({ taskId: task!.id });
                useSetTaskState({ id: task!.id, eventType: 'closed' });
                onRedirectAfterFinish();
            } catch {
                (e: Error) => console.error(e);
            }
        }
    };

    const onCurrentPageChange = (page: number) => {
        setCurrentPage(page);
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
        onAddTouchedPage: validationValues.onAddTouchedPage,
        setSelectedAnnotation,
        validPages: validationValues.validPages,
        setValidPages: validationValues.setValidPages,
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
        const latestLabelIds = latestAnnotationsResult.data.categories;

        setLatestLabelsId(latestLabelIds);

        const result = mapAnnotationPagesFromApi(
            (page: PageInfo) => page.page_num.toString(),
            latestAnnotationsResult.data.pages,
            categories
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
    }, [latestAnnotationsResult.data, categories, mapAnnotationPagesFromApi]);

    const onClearModifiedPages = useCallback(async () => {
        setModifiedPages([]);
    }, []);

    const syncScroll = useSyncScroll();

    const linksFromApi = latestAnnotationsResult.data?.links_json;

    const documentLinksValues = useDocumentLinks(linksFromApi);

    const value = useMemo<ContextValue>(() => {
        return {
            task,
            job,
            getJobId,
            categories,
            categoriesLoading,
            selectedCategory,
            selectedLink,
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
            onClearModifiedPages,
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
            selectedLabels,
            onLabelsSelected,
            isDocLabelsModified,
            setSelectedLabels,
            latestLabelsId,
            setLatestLabelsId,
            linksFromApi,
            ...splitValidation,
            ...syncScroll,
            ...documentLinksValues,
            ...validationValues
        };
    }, [
        task,
        job,
        categories,
        categoriesLoading,
        selectedCategory,
        selectedLink,
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
        isDataTabDisabled,
        selectedToolParams,
        splitValidation,
        syncScroll,
        selectedLabels,
        latestLabelsId,
        linksFromApi,
        documentLinksValues,
        latestAnnotationsResult,
        validationValues
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
