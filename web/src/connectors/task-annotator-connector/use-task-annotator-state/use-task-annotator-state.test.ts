import { useTaskAnnotatorState } from './use-task-annotator-state';
import { act, renderHook } from '@testing-library/react-hooks';
import {
    CHANGE_ANN_DATA_ATTRS,
    CREATE_ANNOTATION,
    defaultExternalViewer,
    DELETE_ANNOTATION,
    DELETE_ANNOTATION_LINK,
    MODIFY_ANNOTATION,
    ON_TABLE_DOUBLE_CLICK,
    SET_ALL_ANNOTATIONS,
    SET_CURRENT_DOCUMENT_USER_ID,
    SET_LATEST_LABELS_ID,
    SET_SELECTED_ANNOTATION,
    SET_SELECTED_ANN_DATA_ATTRS,
    SET_SELECTED_CATEGORY,
    SET_SELECTED_LABELS,
    SET_SELECTED_TOOL,
    SET_STORED_PARAMS,
    SET_TAB_VALUE,
    SET_UNDO_LIST,
    SWAP_UNDO_LIST_ANNOTATION_STATE,
    UNSELECT_ANNOTATION
} from './constants';
import { Annotation, PaperToolParams, ToolNames } from 'shared';
import { CategoryDataAttribute, Link } from 'api/typings';
import { TUndoItem } from './types';

const category = {
    id: 'category-id',
    name: 'category-name',
    parent: null,
    isLeaf: false
};

const link = { category_id: 'category_id', page_num: 1, to: 'to-id', type: 'directional' } as Link;

const annotation = {
    id: 'id',
    links: [link],
    boundType: 'box',
    bound: { x: 0, y: 0, width: 0, height: 0 }
} as Annotation;

const annotationTable = {
    id: 'id',
    boundType: 'table',
    children: [annotation.id],
    bound: { x: 0, y: 0, width: 0, height: 0 }
} as Annotation;

describe('use-task-annotator-state', () => {
    it('Must set proper documentId', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].currentDocumentUserId).not.toBeDefined();
        act(() => result.current[1]({ type: SET_CURRENT_DOCUMENT_USER_ID, payload: 'documentId' }));
        expect(result.current[0].currentDocumentUserId).toBe('documentId');
    });
    it('Must set proper selected category', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedCategory).not.toBeDefined();
        act(() => result.current[1]({ type: SET_SELECTED_CATEGORY, payload: category }));
        expect(result.current[0].selectedCategory).toBe(category);
    });
    it('Must set proper selected category', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedCategory).not.toBeDefined();
        act(() => result.current[1]({ type: SET_SELECTED_CATEGORY, payload: category }));
        expect(result.current[0].selectedCategory).toBe(category);
    });
    it('Must set selected labels without latestLabelsId', () => {
        const selectedLabels = [{ id: 'id', name: 'name' }];

        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedLabels).toHaveLength(0);
        expect(result.current[0].isDocLabelsModified).toBeFalsy();

        act(() => result.current[1]({ type: SET_SELECTED_LABELS, payload: selectedLabels }));

        expect(result.current[0].selectedLabels).toStrictEqual(selectedLabels);
        expect(result.current[0].isDocLabelsModified).toBeTruthy();
    });
    it('Must set selected labels with latestLabelsId', () => {
        const latestLabelsId = ['id'];
        const selectedLabels = [{ id: 'id', name: 'name' }];
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedLabels).toHaveLength(0);
        expect(result.current[0].latestLabelsId).toHaveLength(0);
        expect(result.current[0].isDocLabelsModified).toBeFalsy();

        act(() => result.current[1]({ type: SET_LATEST_LABELS_ID, payload: latestLabelsId }));

        expect(result.current[0].latestLabelsId).toStrictEqual(latestLabelsId);

        act(() => result.current[1]({ type: SET_SELECTED_LABELS, payload: selectedLabels }));

        expect(result.current[0].selectedLabels).toStrictEqual(selectedLabels);
        expect(result.current[0].isDocLabelsModified).toBeFalsy();
    });
    it('Must unselect annotation', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() => result.current[1]({ type: SET_SELECTED_ANNOTATION, payload: annotation }));
        act(() => result.current[1]({ type: SET_TAB_VALUE, payload: 'Data' }));

        expect(result.current[0].selectedAnnotation).toBe(annotation);
        expect(result.current[0].isCategoryDataEmpty).toBeFalsy();
        expect(result.current[0].tabValue).toBe('Data');

        act(() => result.current[1]({ type: UNSELECT_ANNOTATION, payload: undefined }));

        expect(result.current[0].selectedAnnotation).toBeUndefined();
        expect(result.current[0].isCategoryDataEmpty).toBeTruthy();
        expect(result.current[0].tabValue).toBe('Categories');
    });
    it('Must create annotation', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedAnnotation).not.toBeDefined();
        expect(result.current[0].tableMode).toBeFalsy();
        expect(result.current[0].modifiedPages).toHaveLength(0);
        expect(result.current[0].allAnnotations).toStrictEqual({});

        act(() =>
            result.current[1]({ type: CREATE_ANNOTATION, payload: { pageNum: 1, annotation } })
        );

        expect(result.current[0].selectedAnnotation).toBe(annotation);
        expect(result.current[0].tableMode).toBeFalsy();
        expect(result.current[0].modifiedPages).toStrictEqual([1]);
        expect(result.current[0].allAnnotations).toStrictEqual({ 1: [annotation] });

        act(() =>
            result.current[1]({
                type: CREATE_ANNOTATION,
                payload: { pageNum: 1, annotation: annotationTable }
            })
        );

        expect(result.current[0].selectedAnnotation).toBe(annotationTable);
        expect(result.current[0].tableMode).toBeTruthy();
        expect(result.current[0].modifiedPages).toStrictEqual([1]);
        expect(result.current[0].allAnnotations).toStrictEqual({
            1: [annotation, annotationTable]
        });
    });
    it('Must delete annotation', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() => result.current[1]({ type: SET_ALL_ANNOTATIONS, payload: { 1: [annotation] } }));

        expect(result.current[0].modifiedPages).toHaveLength(0);
        expect(result.current[0].allAnnotations).toStrictEqual({ 1: [annotation] });

        act(() =>
            result.current[1]({
                type: DELETE_ANNOTATION,
                payload: { pageNum: 1, annotationId: annotation.id }
            })
        );

        expect(result.current[0].modifiedPages).toStrictEqual([1]);
        expect(result.current[0].allAnnotations).toStrictEqual({ 1: [] });

        act(() =>
            result.current[1]({
                type: SET_ALL_ANNOTATIONS,
                payload: { 1: [annotation, annotationTable] }
            })
        );

        expect(result.current[0].allAnnotations).toStrictEqual({
            1: [annotation, annotationTable]
        });

        act(() =>
            result.current[1]({
                type: DELETE_ANNOTATION,
                payload: { pageNum: 1, annotationId: annotationTable.id }
            })
        );

        expect(result.current[0].allAnnotations).toStrictEqual({ 1: [] });
    });
    it('Must modify annotation', () => {
        const newBound = { x: 1, y: 1, width: 0, height: 0 };

        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() => result.current[1]({ type: SET_ALL_ANNOTATIONS, payload: { 1: [annotation] } }));

        expect(result.current[0].modifiedPages).toHaveLength(0);

        act(() =>
            result.current[1]({
                type: MODIFY_ANNOTATION,
                payload: {
                    pageNum: 1,
                    annotationId: annotation.id,
                    changes: { bound: newBound }
                }
            })
        );

        expect(result.current[0].modifiedPages).toHaveLength(1);
        expect(result.current[0].modifiedPages[0]).toBe(1);
        expect(result.current[0].allAnnotations['1'][0]).toStrictEqual({
            ...annotation,
            bound: newBound
        });

        act(() =>
            result.current[1]({
                type: MODIFY_ANNOTATION,
                payload: {
                    pageNum: -1,
                    annotationId: annotation.id,
                    changes: { bound: annotation.bound }
                }
            })
        );

        expect(result.current[0].modifiedPages).toHaveLength(1);
        expect(result.current[0].modifiedPages[0]).toBe(1);
        expect(result.current[0].allAnnotations['1'][0]).toStrictEqual(annotation);
    });
    it('Must delete annotation link', () => {
        const wrongLink = { ...link, to: 'wrong-direction' };

        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() => result.current[1]({ type: SET_ALL_ANNOTATIONS, payload: { 1: [annotation] } }));

        expect(result.current[0].allAnnotations['1'][0].links).toHaveLength(1);

        act(() =>
            result.current[1]({
                type: DELETE_ANNOTATION_LINK,
                payload: {
                    pageNum: 1,
                    link: wrongLink,
                    annotationId: annotation.id
                }
            })
        );

        expect(result.current[0].allAnnotations['1'][0].links).toHaveLength(1);

        act(() =>
            result.current[1]({
                type: DELETE_ANNOTATION_LINK,
                payload: {
                    link,
                    pageNum: 1,
                    annotationId: annotation.id
                }
            })
        );

        expect(result.current[0].allAnnotations['1'][0].links).toHaveLength(0);
    });
    it('Must set selected annotation data attributes with founded category data attrs', () => {
        const foundCategoryDataAttrs = {
            type: 'text',
            name: 'textDataAttr'
        } as CategoryDataAttribute;

        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].tabValue).toBe('Categories');
        expect(result.current[0].isCategoryDataEmpty).toBeFalsy();
        expect(result.current[0].selectedAnnotation).not.toBeDefined();
        expect(result.current[0].annDataAttrs).toStrictEqual({});

        act(() =>
            result.current[1]({
                type: SET_SELECTED_ANN_DATA_ATTRS,
                payload: { annotation, foundCategoryDataAttrs: [foundCategoryDataAttrs] }
            })
        );

        expect(result.current[0].tabValue).toBe('Data');
        expect(result.current[0].isCategoryDataEmpty).toBeFalsy();
        expect(result.current[0].selectedAnnotation).toStrictEqual(annotation);
        expect(result.current[0].annDataAttrs[annotation.id][0].name).toBe(
            foundCategoryDataAttrs.name
        );
        expect(result.current[0].annDataAttrs[annotation.id][0].type).toBe(
            foundCategoryDataAttrs.type
        );
        expect(result.current[0].annDataAttrs[annotation.id][0].value).toBe('');
    });
    it('Must set selected annotation data attributes without founded category data attrs', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() =>
            result.current[1]({
                type: SET_TAB_VALUE,
                payload: 'Data'
            })
        );

        expect(result.current[0].tabValue).toBe('Data');
        expect(result.current[0].isCategoryDataEmpty).toBeFalsy();
        expect(result.current[0].annDataAttrs).toStrictEqual({});

        act(() =>
            result.current[1]({
                type: SET_SELECTED_ANN_DATA_ATTRS,
                payload: { annotation, foundCategoryDataAttrs: [] }
            })
        );

        expect(result.current[0].tabValue).toBe('Categories');
        expect(result.current[0].isCategoryDataEmpty).toBeTruthy();
        expect(result.current[0].annDataAttrs).toStrictEqual({});
    });
    it('Must change selected annotation data attributes', () => {
        const textCategoryDataAttrs = {
            type: 'text',
            name: 'textDataAttr'
        } as CategoryDataAttribute;
        const moleculeCategoryDataAttrs = {
            type: 'molecule',
            name: 'textDataAttr'
        } as CategoryDataAttribute;

        const { result } = renderHook(() => useTaskAnnotatorState());

        act(() =>
            result.current[1]({
                type: SET_SELECTED_ANN_DATA_ATTRS,
                payload: {
                    annotation,
                    foundCategoryDataAttrs: [textCategoryDataAttrs, moleculeCategoryDataAttrs]
                }
            })
        );

        expect(result.current[0].externalViewer).toBe(defaultExternalViewer);

        act(() =>
            result.current[1]({
                type: CHANGE_ANN_DATA_ATTRS,
                payload: { index: 0, value: 'newDataAttrValue' }
            })
        );

        expect(result.current[0].externalViewer).toBe(defaultExternalViewer);
        expect(result.current[0].annDataAttrs[annotation.id][0].name).toBe(
            textCategoryDataAttrs.name
        );
        expect(result.current[0].annDataAttrs[annotation.id][0].type).toBe(
            textCategoryDataAttrs.type
        );
        expect(result.current[0].annDataAttrs[annotation.id][0].value).toBe('newDataAttrValue');

        act(() =>
            result.current[1]({
                type: CHANGE_ANN_DATA_ATTRS,
                payload: { index: 1, value: 'moleculeDataAttrValue' }
            })
        );

        expect(result.current[0].externalViewer.value).toBe('moleculeDataAttrValue');
        expect(result.current[0].externalViewer.isOpen).toBeTruthy();
        expect(result.current[0].externalViewer.type).toBe(moleculeCategoryDataAttrs.type);
        expect(result.current[0].externalViewer.name).toBe(moleculeCategoryDataAttrs.name);

        expect(result.current[0].annDataAttrs[annotation.id][1].name).toBe(
            moleculeCategoryDataAttrs.name
        );
        expect(result.current[0].annDataAttrs[annotation.id][1].type).toBe(
            moleculeCategoryDataAttrs.type
        );
        expect(result.current[0].annDataAttrs[annotation.id][1].value).toBe(
            'moleculeDataAttrValue'
        );
    });
    it('Must set stored params', () => {
        const toolParams = {
            type: 'slider',
            values: { radius: { value: 0, bounds: { min: 0, max: 0 } } }
        } as PaperToolParams;

        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].selectedTool).toBe(ToolNames.pen);

        act(() =>
            result.current[1]({
                type: SET_SELECTED_TOOL,
                payload: ToolNames.brush
            })
        );

        expect(result.current[0].selectedTool).toBe(ToolNames.brush);

        act(() =>
            result.current[1]({
                type: SET_STORED_PARAMS,
                payload: toolParams
            })
        );

        expect(result.current[0].storedParams[ToolNames.brush]).toStrictEqual(toolParams);
    });
    it('Must swap undo list state', () => {
        const undoItem = {
            annotation,
            action: 'add',
            pageNumber: 1
        } as TUndoItem;

        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].undoList).toHaveLength(0);

        act(() =>
            result.current[1]({
                type: SET_UNDO_LIST,
                payload: [undoItem]
            })
        );

        expect(result.current[0].undoList).toHaveLength(1);
        expect(result.current[0].undoList[0].annotation).toStrictEqual(annotation);

        act(() =>
            result.current[1]({
                type: SWAP_UNDO_LIST_ANNOTATION_STATE,
                payload: { undoPointer: 0, annotation: annotationTable }
            })
        );

        expect(result.current[0].undoList).toHaveLength(1);
        expect(result.current[0].undoList[0].annotation).toStrictEqual(annotationTable);
    });
    it('Must change state on table double click', () => {
        const { result } = renderHook(() => useTaskAnnotatorState());

        expect(result.current[0].tableMode).toBeFalsy();
        expect(result.current[0].tabValue).toBe('Categories');
        expect(result.current[0].selectedAnnotation).not.toBeDefined();

        act(() =>
            result.current[1]({
                type: ON_TABLE_DOUBLE_CLICK,
                payload: annotation
            })
        );

        expect(result.current[0].tableMode).toBeTruthy();
        expect(result.current[0].tabValue).toBe('Data');
        expect(result.current[0].selectedAnnotation).toBeDefined();
        expect(result.current[0].selectedAnnotation).toStrictEqual(annotation);
    });
});
