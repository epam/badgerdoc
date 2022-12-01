import React, {
    CSSProperties,
    FC,
    PropsWithChildren,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from 'react';
import styles from './annotator.module.scss';
import noop from 'lodash/noop';
import { AnnotationsLayer } from './layers/annotations-layer/annotations-layer';
import { SelectionLayer } from './layers/selection-layer/selection-layer';
import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageTool,
    AnnotationImageToolType,
    AnnotationLabel,
    AnnotationsStyle,
    Bound,
    PageToken,
    PaperTool,
    TokenStyle
} from './typings';
import { TokensLayer } from './layers/tokens-layer/tokens-layer';
import { editableAnnotationRenderer } from './layers/annotations-layer/annotations-editable-renderer';
import { useSelection } from './hooks/use-selection';
import { useBoxResize } from './hooks/use-box-resize';
import { ANNOTATION_LABEL_CLASS, useAnnotationMove } from './hooks/use-annotation-move';
import { useSubmitAnnotation } from './hooks/use-submit-annotation';
import { downScaleCoords } from './utils/down-scale-coords';
import { useAnnotationsClick } from './hooks/use-annotations-click';
import {
    useAnnotationsTokens,
    useSelectionTokens,
    useTokensByResizing
} from './hooks/use-active-tokens-calculation';
import { Category } from '../../../api/typings';
import { arrayUniqueByKey } from './utils/unique-array';
import { useTaskAnnotatorContext } from '../../../connectors/task-annotator-connector/task-annotator-context';
import { AnnotationLinksBoundType } from 'shared';

import { useTableAnnotatorContext } from './context/table-annotator-context';
import { scaleAnnotation } from './utils/scale-annotation';
import { updateAnnotation } from './components/table-annotation/helpers';

import paper from 'paper';
import { createImageTool } from './components/image-tools';
import { removeAllSelections } from './components/image-tools/utils';

const resizeSelectionCast = {
    box: 'free-box',
    'free-box': 'free-box',
    text: 'text'
} as Record<
    AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType,
    AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
>;

export type AnnotatorProps = PropsWithChildren<{
    // --- Callbacks --- //

    onAnnotationAdded?: (ann: Pick<Annotation, 'bound' | 'boundType' | 'id'>) => void;
    onAnnotationContextMenu?: (
        event: React.MouseEvent,
        annotationId: string | number,
        labels?: AnnotationLabel[]
    ) => void;
    onAnnotationDeleted?: (annotationId: string | number) => void;
    onAnnotationEdited?: (annotationId: string | number, changes: Partial<Annotation>) => void;
    onEmptyAreaClick: () => void;
    onAnnotationDoubleClick: (annotation: Annotation) => void;
    onAnnotationCopyPress: (annotationId: string | number) => void;
    onAnnotationCutPress: (annotationId: string | number) => void;
    onAnnotationPastePress: () => void;
    onAnnotationUndoPress: () => void;
    onAnnotationRedoPress: () => void;

    // --- Props --- //

    scale: number;
    selectionType?: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType;
    annotations: Annotation[];
    tokens?: PageToken[];
    annotationSpan?: number;
    selectedCategory?: Category;
    categories?: Category[];
    isCellMode: boolean;
    page: number;
    editable: boolean;

    // --- Customization --- //

    annotationStyle?: AnnotationsStyle;
    selectionStyle?: CSSProperties;
    tokenStyle?: TokenStyle;
}>;

export const Annotator: FC<AnnotatorProps> = ({
    children,
    scale,
    tokens = [],
    editable,
    annotations,
    tokenStyle,
    annotationStyle,
    selectionStyle,
    selectionType = 'box',
    onAnnotationAdded = noop,
    onAnnotationContextMenu = noop,
    onAnnotationDeleted,
    onAnnotationEdited = noop,
    selectedCategory,
    categories = [],
    isCellMode,
    onEmptyAreaClick,
    onAnnotationDoubleClick = noop,
    page,
    onAnnotationCopyPress = noop,
    onAnnotationCutPress = noop,
    onAnnotationPastePress = noop,
    onAnnotationUndoPress = noop,
    onAnnotationRedoPress = noop
}) => {
    const {
        isNeedToSaveTable,
        setIsNeedToSaveTable,
        selectedAnnotation,
        fileMetaInfo,
        selectedTool,
        setSelectedTool,
        selectedToolParams,
        setSelectedAnnotation,
        taskHasTaxonomies
    } = useTaskAnnotatorContext();

    const { setTableModeRows, setTableModeColumns } = useTableAnnotatorContext();
    const selectedAnnotationRef = useRef<HTMLDivElement>(null);

    const [hoveredAnnotation, setHoveredAnnotation] = useState<Annotation>();
    const createdIdRef = useRef<number | null>(null);
    const [deleteId, setDeleteId] = useState<number>();

    const [tools, setTools] = useState<AnnotationImageTool>({
        pen: undefined,
        brush: undefined,
        dextr: undefined,
        eraser: undefined,
        rectangle: undefined,
        wand: undefined,
        select: undefined
    });
    const [paperIsSet, setPaperIsSet] = useState<boolean>(false);

    const panoRef = useRef<HTMLDivElement>(null);
    const unSelectAnnotation = () => {
        onEmptyAreaClick && onEmptyAreaClick();
        setSelectedAnnotation(undefined);
    };
    const onClickHook = useAnnotationsClick(
        panoRef,
        annotations,
        scale,
        ['box', 'free-box', 'table', 'text'],
        setSelectedAnnotation,
        unSelectAnnotation
    );

    const { coords: selectionCoords, isEnded: isSelectionEnded } = useSelection(
        panoRef,
        selectionType,
        isCellMode,
        editable
    );

    const submitAnnotation = useSubmitAnnotation(
        selectionType,
        tokens,
        (annBound: Pick<Annotation, 'bound' | 'boundType'>) => {
            createdIdRef.current = Date.now();
            onAnnotationAdded({ id: createdIdRef.current, ...annBound } as any);
        }
    );

    const submitResizedAnnotation = useSubmitAnnotation(
        resizeSelectionCast[selectionType],
        tokens,
        (ann) => selectedAnnotation && onAnnotationEdited(selectedAnnotation.id, ann)
    );

    const submitMovedAnnotation = useSubmitAnnotation(
        resizeSelectionCast[selectionType],
        tokens,
        (ann) => selectedAnnotation && onAnnotationEdited(selectedAnnotation.id, ann)
    );

    const { coords: resizedBoxAnnotationCoords, isEnded: isBoxAnnotationResizeEnded } =
        useBoxResize({
            panoRef,
            selectedAnnotationRef,
            selectedAnnotation
        });

    const { coords: movedAnnotationCoords, isEnded: isAnnotationMoveEnded } = useAnnotationMove({
        panoRef,
        selectedAnnotationRef,
        selectedAnnotation,
        isEditable: editable
    });

    const selectionTokens = useSelectionTokens({
        selectionCoords,
        tokens,
        scale,
        selectionType
    });

    const scaledClickedAnnotation = annotations.find((ann) => ann.id === selectedAnnotation?.id);

    const clickedAnnotationTokens = useAnnotationsTokens({
        tokens,
        annotations: scaledClickedAnnotation ? [scaledClickedAnnotation] : []
    });

    const scaledHoveredAnnotation = annotations.find((ann) => ann.id === hoveredAnnotation?.id);

    const hoveredAnnotationTokens = useAnnotationsTokens({
        tokens,
        annotations: scaledHoveredAnnotation ? [scaledHoveredAnnotation] : []
    });
    const tokensByResizing = useTokensByResizing({
        tokens,
        resizedBoxAnnotationCoords,
        scale
    });

    const activeTokens = useMemo(() => {
        return arrayUniqueByKey(
            [
                ...clickedAnnotationTokens,
                ...hoveredAnnotationTokens,
                ...selectionTokens,
                ...tokensByResizing
            ],
            'id'
        );
    }, [clickedAnnotationTokens, selectionTokens, tokensByResizing]);

    const paperjs2coco = (width: number, height: number, path: paper.CompoundPath): number[][] => {
        const segments: number[][] = [[]];
        let children = [];
        if ('segments' in path) {
            children = [path as paper.Path];
        } else {
            children = path.children;
        }

        let i = 0;
        for (let child of children) {
            segments[i] = [];
            const childSegments = (child as paper.Path).segments;
            for (let segment of childSegments) {
                segments[i].push(segment.point.x / scale, segment.point.y / scale);
            }
            i++;
        }

        return segments;
    };

    /** Submit Annotation from selection when it's ended */
    useEffect(() => {
        if (isSelectionEnded && selectionCoords.length) {
            setTableModeRows(1);
            setTableModeColumns(1);
            if (selectionType !== 'polygon')
                submitAnnotation(downScaleCoords(selectionCoords, scale));
        }
        if (
            (isSelectionEnded && selectionType === 'polygon' && selectionCoords.length) ||
            (selectionType === 'polygon' && selectedTool === 'wand')
        ) {
            if (tools[selectedTool]) {
                let path: paper.Path;
                if (selectedTool === 'eraser' || selectedTool === 'brush') {
                    path = tools[selectedTool]!.selection!;
                } else {
                    path = tools[selectedTool]!.path;
                }
                if (!path || !Object.values(path).length) return;
                //path.simplify(); //TODO: is it necessary?
                let isNeedToEdit = false;
                let annId;
                let isSomethingSelected: boolean = false;

                for (let child of paper.project.activeLayer.children) {
                    if (child.data.isSelected) {
                        isSomethingSelected = true;
                        if (selectedTool !== 'eraser')
                            path = path.unite(child as paper.Path) as paper.Path;
                        else {
                            path = (child as paper.CompoundPath).subtract(path) as paper.Path;
                            isNeedToEdit = true;
                            annId = child.data.annotationId;
                            break; //TODO: infinite loop without this break why?
                        }
                        isNeedToEdit = true;
                        annId = child.data.annotationId;
                    }
                }
                if (selectedTool === 'eraser' && !isSomethingSelected) return;
                const newTool: PaperTool = {
                    tool: tools[selectedTool]!.tool,
                    path: path,
                    cocoSegments: paperjs2coco(
                        fileMetaInfo.imageSize!.width,
                        fileMetaInfo.imageSize!.height,
                        path
                    ),
                    params: {
                        type: 'slider-number',
                        values: {} as any
                    }
                };
                if (newTool.cocoSegments.length === 0) return;
                if (isNeedToEdit) {
                    const bound: Bound = {
                        x: newTool.path.bounds.x,
                        y: newTool.path.bounds.y,
                        width: newTool.path.bounds.width,
                        height: newTool.path.bounds.height
                    };
                    const ann = {
                        boundType: 'polygon' as AnnotationBoundType,
                        bound: bound,
                        segments: newTool.cocoSegments
                    };
                    removeAllSelections();
                    onAnnotationEdited(+annId, ann);
                } else {
                    submitAnnotation(newTool);
                }
            }
        }
    }, [selectionCoords, isSelectionEnded]);
    useEffect(() => {
        if (createdIdRef.current) {
            const createdAnnotation = annotations.find((ann) => ann.id === createdIdRef.current);
            if (createdAnnotation) {
                setSelectedAnnotation(scaleAnnotation(createdAnnotation, scale));
            }
            createdIdRef.current = null;
        }
    }, [annotations]);

    /** Submit Box Annotation when resizing is ended */
    useEffect(() => {
        if (isBoxAnnotationResizeEnded && resizedBoxAnnotationCoords.length) {
            submitResizedAnnotation(downScaleCoords(resizedBoxAnnotationCoords, scale));
        }
    }, [resizedBoxAnnotationCoords, isBoxAnnotationResizeEnded]);

    useEffect(() => {
        if (isAnnotationMoveEnded && movedAnnotationCoords.length) {
            submitMovedAnnotation(downScaleCoords(movedAnnotationCoords, scale));
        }
    }, [movedAnnotationCoords, isAnnotationMoveEnded]);

    useEffect(() => {
        if (
            selectedAnnotation &&
            isNeedToSaveTable.gutters &&
            isNeedToSaveTable.cells &&
            isNeedToSaveTable.cells.length
        ) {
            const ann = {
                ...selectedAnnotation,
                table: updateAnnotation(selectedAnnotation, isNeedToSaveTable.gutters, scale),
                children: isNeedToSaveTable.cells.map((el) => el.id),
                tableCells: isNeedToSaveTable.cells.map((el) => downscaleAnnotation(el))
            };
            onAnnotationEdited(selectedAnnotation.id, ann);
            setIsNeedToSaveTable({
                gutters: undefined,
                cells: undefined
            });
        }
    }, [selectedAnnotation, isNeedToSaveTable]);

    const downscaleAnnotation = (a: Annotation): Annotation => {
        return {
            ...a,
            bound: {
                x: a.bound.x / scale,
                y: a.bound.y / scale,
                width: a.bound.width / scale,
                height: a.bound.height / scale
            }
        };
    };

    const [size, setSize] = useState<{ width: number; height: number }>();
    useEffect(() => {
        if (fileMetaInfo.imageSize) {
            setSize(fileMetaInfo.imageSize);
        }
    }, [fileMetaInfo.imageSize]);

    useEffect(() => {
        if (deleteId) {
            onAnnotationDeleted?.(+deleteId);
        }
    }, [deleteId]);

    function useHookWithRefCallback() {
        const ref = useRef(null);
        const setRef = useCallback((node) => {
            if (node) {
                paper.setup(node as HTMLCanvasElement);
                setPaperIsSet(true);

                if (selectionType === 'polygon') {
                    const defaultActivePen = createImageTool(
                        'pen',
                        onAnnotationDeleted,
                        selectedToolParams
                    );

                    defaultActivePen!.tool.activate();
                    setTools({
                        ...tools,
                        pen: defaultActivePen
                    });
                }
            }

            ref.current = node;
        }, []);

        return [setRef];
    }

    const [cR] = useHookWithRefCallback();

    useEffect(() => {
        if (selectionType === 'polygon') {
            const newTool = createImageTool(selectedTool, setDeleteId, selectedToolParams);
            newTool!.tool.activate();
            if (tools[selectedTool]) {
                if (tools[selectedTool]!.tool) tools[selectedTool]!.tool.remove();
                if (Object.values(tools[selectedTool]!.path).length)
                    tools[selectedTool]!.path.remove();
            }
            setTools({
                ...tools,
                [selectedTool]: newTool
            });
        } else {
            if (tools[selectedTool]) {
                if (tools[selectedTool]!.tool) tools[selectedTool]!.tool.remove();
                if (Object.values(tools[selectedTool]!.path).length)
                    tools[selectedTool]!.path.remove();
            }
            setTools({
                ...tools,
                [selectedTool]: undefined
            });
        }
    }, [selectedTool, selectionType, selectedToolParams]);

    return (
        <div className={`${styles.container} annotations`}>
            <div
                role="none"
                ref={panoRef}
                onClick={(e) => {
                    if ((e.target as HTMLElement).classList.contains(ANNOTATION_LABEL_CLASS)) {
                        return;
                    }
                    onClickHook(e);
                }}
            >
                <AnnotationsLayer
                    annotationsStyle={annotationStyle}
                    annotations={annotations}
                    scale={scale}
                    onAnnotationCopyPress={() => onAnnotationCopyPress(selectedAnnotation?.id)}
                    onAnnotationCutPress={() => onAnnotationCutPress(selectedAnnotation?.id)}
                    onAnnotationPastePress={onAnnotationPastePress}
                    onAnnotationUndoPress={onAnnotationUndoPress}
                    onAnnotationRedoPress={onAnnotationRedoPress}
                    renderAnnotation={({ annotation }) => {
                        const isSelected = annotation.id === selectedAnnotation?.id;
                        const isHovered = annotation.id === hoveredAnnotation?.id;
                        return editableAnnotationRenderer({
                            annotation,
                            cells: annotation.tableCells,
                            isSelected,
                            isHovered,
                            scale,
                            panoRef,
                            isCellMode,
                            editable,
                            categories,
                            tools,
                            canvas: paperIsSet,
                            setTools,
                            onClick: (e) => {
                                onClickHook(e, annotation);
                            },
                            onDoubleClick: () => {
                                onAnnotationDoubleClick(
                                    annotation.boundType === 'table'
                                        ? downscaleAnnotation(annotation)
                                        : annotation
                                );
                            },
                            onContextMenu: (e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                onAnnotationContextMenu(e, annotation.id, annotation.labels);
                                onClickHook(e, annotation);
                            },
                            onAnnotationContextMenu: (
                                event: React.MouseEvent<HTMLDivElement>,
                                annotationId: string | number,
                                labels?: AnnotationLabel[]
                            ) => {
                                onAnnotationContextMenu(event, annotationId, labels);
                                onClickHook(event, annotation);
                            },
                            onCloseIconClick: () => {
                                setSelectedAnnotation(undefined);
                                onAnnotationDeleted?.(annotation.id);
                            },
                            onAnnotationDelete: (id: string | number) => {
                                setSelectedAnnotation(undefined);
                                onAnnotationDeleted?.(id);
                            },
                            page,
                            onMouseEnter: () => setHoveredAnnotation(annotation),
                            onMouseLeave: () => setHoveredAnnotation(undefined),
                            selectedAnnotationRef: isSelected ? selectedAnnotationRef : undefined,
                            taskHasTaxonomies
                        });
                    }}
                    page={page}
                    categories={categories}
                >
                    {size && fileMetaInfo.extension === '.jpg' && Object.values(size).length > 0 && (
                        <canvas
                            ref={cR}
                            id="canvas"
                            style={{
                                position: 'absolute',
                                width: fileMetaInfo.imageSize?.width,
                                height: fileMetaInfo.imageSize?.height,
                                zIndex: 11 //TODO: 100?
                            }}
                        />
                    )}
                    {children}
                    {/* ADD STYLING SELECTED AND ANNOTATIONS TOKENS LATER */}
                    <TokensLayer tokens={activeTokens} scale={scale} tokenStyle={tokenStyle} />
                </AnnotationsLayer>
            </div>
            <SelectionLayer
                selectionType={selectionType}
                selectionCoords={selectionCoords}
                selectionStyle={selectionStyle}
                isSelectionEnded={isSelectionEnded}
                multilineTextProps={{
                    tokens: selectionTokens,
                    scale: scale,
                    color: tokenStyle?.background as string,
                    label: selectedCategory?.name as string
                }}
                page={page}
            />
        </div>
    );
};
