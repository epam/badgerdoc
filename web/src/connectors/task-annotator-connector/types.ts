import { Task } from 'api/typings/tasks';
import { ApiError } from 'api/api-error';
import {
    Category,
    CategoryDataAttribute,
    CategoryDataAttributeWithValue,
    ExternalViewerState,
    Label,
    Link
} from 'api/typings';
import { Job } from 'api/typings/jobs';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';

import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType,
    Maybe,
    PageToken,
    PaperToolParams,
    TableGutterMap,
    ToolNames
} from 'shared';
import { SyncScrollValue } from 'shared/hooks/use-sync-scroll';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import { DocumentLinksValue } from './use-document-links';
import { ValidationValues } from './use-validation';
import { SplitValidationValue } from './use-split-validation';
import {
    CHANGE_ANN_DATA_ATTRS,
    CLOSE_EXTERNAL_VIEWER,
    CREATE_ANNOTATION,
    DELETE_ANNOTATION,
    DELETE_ANNOTATION_LINK,
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

export type ContextValue = SplitValidationValue &
    SyncScrollValue &
    DocumentLinksValue &
    Omit<ValidationValues, 'allValid' | 'setValidPages' | 'setAnnotationSaved'> & {
        task?: Task;
        job?: Job;
        categories?: Category[];
        selectedCategory?: Category;
        selectedAnnotation?: Annotation;
        fileMetaInfo: FileMetaInfo;
        tokensByPages: Record<string, PageToken[]>;
        allAnnotations?: Record<string, Annotation[]>;
        pageNumbers: number[];
        currentPage: number;
        modifiedPages: number[];
        pageSize?: { width: number; height: number };
        setPageSize: (pS: any) => void;
        tabValue: string;
        selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType;
        selectedTool: AnnotationImageToolType;
        onChangeSelectedTool: (t: AnnotationImageToolType) => void;
        tableMode: boolean;
        isNeedToSaveTable: {
            gutters?: TableGutterMap;
            cells?: Annotation[];
        };
        setIsNeedToSaveTable: (b: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        }) => void;
        isCategoryDataEmpty: boolean;
        annDataAttrs: Record<string, Array<CategoryDataAttributeWithValue>>;
        externalViewer: ExternalViewerState;
        onChangeSelectionType: (
            newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
        ) => void;
        onCategorySelected: (category: Category) => void;
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
        selectedLabels?: Label[];
        onLabelsSelected: (labels: Label[]) => void;
        latestLabelsId: string[];
        isDocLabelsModified: boolean;
        getJobId: () => number | undefined;
        setCurrentDocumentUserId: (userId?: string) => void;
        currentDocumentUserId?: string;
    };

export type ProviderProps = {
    taskId?: number;
    fileMetaInfo?: FileMetaInfo;
    jobId?: number;
    revisionId?: string;
    onRedirectAfterFinish?: () => void;
    onSaveTaskSuccess?: () => void;
    onSaveTaskError?: (error: ApiError) => void;
};

export type UndoListAction = 'edit' | 'delete' | 'add';

type TUndoItem = { action: UndoListAction; annotation: Annotation; pageNumber: number };

export type TState = {
    undoList: TUndoItem[];
    undoPointer: number;
    currentDocumentUserId?: string;
    selectedCategory?: Category;
    selectedLabels: Label[];
    latestLabelsId: string[];
    isDocLabelsModified: boolean;
    allAnnotations: Record<string, Annotation[]>;
    selectedToolParams: PaperToolParams;
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
        gutters?: TableGutterMap;
        cells?: Annotation[];
    };
    storedParams: Record<ToolNames, PaperToolParams | undefined>;
    pageSize: { width: number; height: number };
};

type TActionGeneric<T, P = undefined> = {
    type: T;
    payload: P;
};

export type TAction =
    | TActionGeneric<typeof SET_CURRENT_DOCUMENT_USER_ID, TState['currentDocumentUserId']>
    | TActionGeneric<typeof SET_SELECTED_CATEGORY, TState['selectedCategory']>
    | TActionGeneric<typeof SET_SELECTED_LABELS, TState['selectedLabels']>
    | TActionGeneric<typeof SET_LATEST_LABELS_ID, TState['latestLabelsId']>
    | TActionGeneric<typeof SET_ALL_ANNOTATIONS, TState['allAnnotations']>
    | TActionGeneric<typeof SET_SELECTED_TOOL_PARAMS, TState['selectedToolParams']>
    | TActionGeneric<typeof SET_CURRENT_PAGE, TState['currentPage']>
    | TActionGeneric<typeof SET_MODIFIED_PAGES, TState['modifiedPages']>
    | TActionGeneric<typeof SET_TAB_VALUE, TState['tabValue']>
    | TActionGeneric<typeof SET_SELECTION_TYPE, TState['selectionType']>
    | TActionGeneric<typeof SET_SELECTED_TOOL, TState['selectedTool']>
    | TActionGeneric<typeof SET_SELECTED_ANNOTATION, TState['selectedAnnotation']>
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
    | TActionGeneric<typeof SET_PAGE_SIZE, TState['pageSize']>
    | TActionGeneric<typeof CREATE_ANNOTATION, { pageNum: number; annotation: Annotation }>
    | TActionGeneric<typeof DELETE_ANNOTATION, { pageNum: number; annotationId: Annotation['id'] }>
    | TActionGeneric<
          typeof MODIFY_ANNOTATION,
          { pageNum: number; id: string | number; changes: Partial<Annotation> }
      >
    | TActionGeneric<
          typeof DELETE_ANNOTATION_LINK,
          { pageNum: number; annotationId: Annotation['id']; link: Link }
      >
    | TActionGeneric<typeof UNSELECT_ANNOTATION>
    | TActionGeneric<typeof SET_UNDO_LIST, TUndoItem[]>
    | TActionGeneric<typeof SET_UNDO_POINTER, number>
    | TActionGeneric<
          typeof SWAP_UNDO_LIST_ANNOTATION_STATE,
          { undoPointer: number; annotation: Annotation }
      >
    | TActionGeneric<typeof ON_TABLE_DOUBLE_CLICK, Annotation>;
