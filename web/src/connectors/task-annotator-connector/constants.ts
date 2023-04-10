import { ExternalViewerState } from 'api/typings';
import { AnnotationBoundType, PaperToolParams, ToolNames } from 'shared';

export const DEFAULT_STORED_PARAMS = {
    brush: undefined,
    dextr: undefined,
    eraser: undefined,
    pen: undefined,
    rectangle: undefined,
    select: undefined,
    wand: undefined
};

export const DEFAULT_PAGE_WIDTH: number = 0;
export const DEFAULT_PAGE_HEIGHT: number = 0;

export const defaultExternalViewer: ExternalViewerState = {
    isOpen: false,
    type: '',
    name: '',
    value: ''
};

export const INITIAL_STATE = {
    undoList: [],
    undoPointer: -1,
    selectedLabels: [],
    latestLabelsId: [],
    isDocLabelsModified: false,
    allAnnotations: {},
    currentPage: 1,
    modifiedPages: [],
    tabValue: 'Categories',
    selectionType: 'free-box' as AnnotationBoundType,
    selectedTool: 'pen' as ToolNames,
    selectedToolParams: {} as PaperToolParams,
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

export const SET_CURRENT_DOCUMENT_USER_ID = 'SET_CURRENT_DOCUMENT_USER_ID';
export const SET_SELECTED_CATEGORY = 'SET_SELECTED_CATEGORY';
export const SET_SELECTED_LABELS = 'SET_SELECTED_LABELS';
export const SET_LATEST_LABELS_ID = 'SET_LATEST_LABELS_ID';
export const SET_ALL_ANNOTATIONS = 'SET_ALL_ANNOTATIONS';

export const CREATE_ANNOTATION = 'CREATE_ANNOTATION';
export const DELETE_ANNOTATION = 'DELETE_ANNOTATION';
export const MODIFY_ANNOTATION = 'MODIFY_ANNOTATION';
export const DELETE_ANNOTATION_LINK = 'DELETE_ANNOTATION_LINK';
export const UNSELECT_ANNOTATION = 'UNSELECT_ANNOTATION';

export const SET_SELECTED_TOOL_PARAMS = 'SET_SELECTED_TOOL_PARAMS';
export const SET_CURRENT_PAGE = 'SET_CURRENT_PAGE';
export const SET_MODIFIED_PAGES = 'SET_MODIFIED_PAGES';
export const SET_TAB_VALUE = 'SET_TAB_VALUE';
export const SET_SELECTION_TYPE = 'SET_SELECTION_TYPE';
export const SET_SELECTED_TOOL = 'SET_SELECTED_TOOL';
export const SET_SELECTED_ANNOTATION = 'SET_SELECTED_ANNOTATION';
export const SET_ANN_DATA_ATTRS = 'SET_ANN_DATA_ATTRS';
export const CHANGE_ANN_DATA_ATTRS = 'CHANGE_ANN_DATA_ATTRS';
export const SET_SELECTED_ANN_DATA_ATTRS = 'SET_SELECTED_ANN_DATA_ATTRS';
export const SET_EXTERNAL_VIEWER = 'SET_EXTERNAL_VIEWER';
export const CLOSE_EXTERNAL_VIEWER = 'CLOSE_EXTERNAL_VIEWER';
export const SET_TABLE_MODE = 'SET_TABLE_MODE';
export const SET_TABLE_CELL_CATEGORY = 'SET_TABLE_CELL_CATEGORY';
export const SET_IS_NEED_TO_SAVE_TABLE = 'SET_IS_NEED_TO_SAVE_TABLE';
export const SET_STORED_PARAMS = 'SET_STORED_PARAMS';
export const SET_PAGE_SIZE = 'SET_PAGE_SIZE';
export const ON_TABLE_DOUBLE_CLICK = 'ON_TABLE_DOUBLE_CLICK';
export const SET_UNDO_LIST = 'SET_UNDO_LIST';
export const SET_UNDO_POINTER = 'SET_UNDO_POINTER';
export const SWAP_UNDO_LIST_ANNOTATION_STATE = 'SWAP_UNDO_LIST_ANNOTATION_STATE';
