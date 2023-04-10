import { Category, Label } from 'api/typings';
import { PaperToolParams, ToolNames } from 'shared';
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
import { isValidCategoryType, mapAnnDataAttrs } from './task-annotator-utils';
import { TAction, TState } from './types';

export const getToolsParams = (
    selectedTool: ToolNames,
    storedParams: Record<ToolNames, PaperToolParams | undefined>
): PaperToolParams | undefined => {
    switch (selectedTool) {
        case 'eraser':
            if (storedParams.eraser) return storedParams.eraser;
            else
                return {
                    type: 'slider-number',
                    values: {
                        radius: { value: 40, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'brush':
            if (storedParams.brush) return storedParams.brush;
            else
                return {
                    type: 'slider-number',
                    values: {
                        radius: { value: 40, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'wand':
            if (storedParams.wand) return storedParams.wand;
            else
                return {
                    type: 'slider-number',
                    values: {
                        threshold: { value: 35, bounds: { min: 0, max: 150 } },
                        deviation: { value: 15, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'dextr':
        case 'rectangle':
        case 'select':
        case 'pen':
            break;
    }
};

export const mapCategoriesIdToCategories = (ids: string[], categories: Category[]) =>
    ids.reduce((accumulator: Label[], id) => {
        const category = categories.find((item) => item.id === id);
        if (category) accumulator.push({ id, name: category.name });

        return accumulator;
    }, []);

export const reducer = (state: TState, action: TAction) => {
    switch (action.type) {
        case SET_CURRENT_DOCUMENT_USER_ID:
            return { ...state, currentDocumentUserId: action.payload };
        case SET_SELECTED_CATEGORY:
            return { ...state, selectedCategory: action.payload };
        case SET_SELECTED_LABELS: {
            const currentLabelsId = action.payload.map((label) => label.id);
            const isDocLabelsModifiedNewVal =
                state.latestLabelsId.toString() === currentLabelsId.toString();

            return {
                ...state,
                isDocLabelsModifiedNewVal,
                selectedLabels: [...state.selectedLabels, ...action.payload]
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
            return { ...state, latestLabelsId: action.payload };
        case SET_ALL_ANNOTATIONS:
            return { ...state, allAnnotations: action.payload };
        case CREATE_ANNOTATION: {
            const { pageNum, annotation } = action.payload;
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
        case DELETE_ANNOTATION: {
            const { pageNum, annotationId } = action.payload;

            const annotation = state.allAnnotations[pageNum]?.find((el) => el.id === annotationId);

            if (!annotation) return state;

            return {
                ...state,
                modifiedPages: state.modifiedPages.includes(pageNum)
                    ? state.modifiedPages
                    : [...state.modifiedPages, pageNum],
                allAnnotations: {
                    ...state.allAnnotations,
                    [pageNum]: state.allAnnotations[pageNum].filter((ann) => {
                        if (
                            annotation.children &&
                            annotation.boundType === 'table' &&
                            annotation.children.includes(ann.id) &&
                            ann.boundType === 'table_cell'
                        ) {
                            return false;
                        }

                        return ann.id !== annotationId;
                    })
                }
            };
        }
        case MODIFY_ANNOTATION: {
            const { pageNum, id, changes } = action.payload;

            let pageNumber: string | number = pageNum;

            if (pageNumber === -1) {
                pageNumber = Object.keys(state.allAnnotations).find((key: string) =>
                    state.allAnnotations[key].find((ann) => ann.id == id)
                )!;
            }

            const pageAnnotations = state.allAnnotations[pageNum] ?? [];

            return {
                ...state,
                modifiedPages: state.modifiedPages.includes(pageNum)
                    ? state.modifiedPages
                    : [...state.modifiedPages, pageNum],
                allAnnotations: {
                    ...state.allAnnotations,
                    [pageNum]: pageAnnotations.map((ann) => {
                        return ann.id !== id ? ann : { ...ann, ...changes };
                    })
                }
            };
        }
        case DELETE_ANNOTATION_LINK: {
            const { pageNum, annotationId, link: linkToDel } = action.payload;

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
                selectedToolParams: action.payload
            };
        case SET_CURRENT_PAGE:
            return { ...state, currentPage: action.payload };
        case SET_MODIFIED_PAGES:
            return { ...state, modifiedPages: action.payload };
        case SET_TAB_VALUE:
            return { ...state, tabValue: action.payload };
        case SET_SELECTION_TYPE:
            return { ...state, selectionType: action.payload };
        case SET_SELECTED_TOOL:
            return { ...state, selectedTool: action.payload };
        case SET_SELECTED_ANNOTATION:
            return { ...state, selectedAnnotation: action.payload };
        case SET_ANN_DATA_ATTRS: {
            return {
                ...state,
                annDataAttrs: action.payload
            };
        }
        case CHANGE_ANN_DATA_ATTRS: {
            const { index, value } = action.payload;

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
            const { annotation, foundCategoryDataAttrs } = action.payload;

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
            return { ...state, externalViewer: action.payload };
        case CLOSE_EXTERNAL_VIEWER:
            return { ...state, externalViewer: INITIAL_STATE.externalViewer };
        case SET_TABLE_MODE:
            return { ...state, tableMode: action.payload };
        case SET_TABLE_CELL_CATEGORY:
            return { ...state, tableCellCategory: action.payload };
        case SET_IS_NEED_TO_SAVE_TABLE:
            return { ...state, isNeedToSaveTable: action.payload };
        case SET_STORED_PARAMS:
            return {
                ...state,
                storedParams: {
                    ...state.storedParams,
                    [state.selectedTool]: action.payload
                }
            };
        case SET_PAGE_SIZE:
            return { ...state, pageSize: action.payload };
        case SET_UNDO_LIST:
            return { ...state, undoList: action.payload };
        case SET_UNDO_POINTER:
            return { ...state, undoPointer: action.payload };
        case SWAP_UNDO_LIST_ANNOTATION_STATE: {
            const { undoPointer, annotation } = action.payload;

            const undoListCopy = [...state.undoList];
            undoListCopy[undoPointer] = {
                ...undoListCopy[undoPointer],
                annotation
            };

            return { ...state, undoList: undoListCopy };
        }
        case ON_TABLE_DOUBLE_CLICK:
            return {
                ...state,
                tableMode: true,
                tabValue: 'Data',
                selectedAnnotation: action.payload
            };
        default:
            return state;
    }
};
