import {
    Category,
    CategoryDataAttribute,
    CategoryDataAttributeWithValue,
    ExternalViewerState,
    Label,
    Link
} from 'api/typings';

import {
    Annotation,
    AnnotationBoundType,
    AnnotationLinksBoundType,
    PaperToolParams,
    TableGutterMap,
    ToolNames
} from 'shared';
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

import { UndoListAction } from '../types';

export type TUndoItem = { action: UndoListAction; annotation: Annotation; pageNumber: number };

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
          { pageNum: number; annotationId: Annotation['id']; changes: Partial<Annotation> }
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
