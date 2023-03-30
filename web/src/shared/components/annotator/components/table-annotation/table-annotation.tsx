import noop from 'lodash/noop';
import React, { useEffect, useRef, useState } from 'react';
import {
    Annotation,
    Bound,
    GutterParams,
    Maybe,
    TableAnnotationProps,
    TableGutter,
    TableGutterMap
} from '../../typings';
import styles from './table-annotation.module.scss';
import { useGutterMove } from '../../hooks/use-gutter-move';
import { useGutterClick } from '../../hooks/use-gutter-click';
import { useCellSelection } from '../../hooks/use-cell-selection';
import { CellSelectionLayer } from './cell-selection-layer';
import { GuttersLayer } from './gutters-layer';
import {
    canMergeSelectedCells,
    canSplitSelectedCells,
    createInitialCells,
    createInitialGutters,
    isRectangularShape,
    isSelectionBounds,
    recalculatePartsBasedOnCells,
    removeMergedCellsAndAddNewCell,
    splitSelectedCells
} from './helpers';
import { TextLabel } from '../text-label';
import { useTableAnnotatorContext } from '../../context/table-annotator-context';
import { TableCellLayer } from './table-cell-layer';
import { useTaskAnnotatorContext } from '../../../../../connectors/task-annotator-connector/task-annotator-context';
import { getAnnotationElementId } from '../../utils/use-annotation-links';

export const TableAnnotation = ({
    label = '',
    color = 'black',
    bound,
    isSelected,
    isEditable,
    onClick = noop,
    onDoubleClick = noop,
    onContextMenu = noop,
    onCloseIconClick = noop,
    panoRef,
    annotation,
    scale,
    isCellMode,
    id,
    page,
    categories
}: TableAnnotationProps) => {
    const {
        tableModeRows,
        tableModeColumns,
        setCellsSelected,
        mergeCells,
        onMergeCellsClicked,
        setTableModeRows,
        setTableModeColumns,
        setSelectedCellsCanBeMerged,
        splitCells,
        onSplitCellsClicked,
        setSelectedCellsCanBeSplitted
    } = useTableAnnotatorContext();
    const { selectedAnnotation, setIsNeedToSaveTable } = useTaskAnnotatorContext();
    const { tableCellCategory, setTableCellCategory } = useTaskAnnotatorContext();
    const { x, y, width, height } = bound;

    const tableRef = useRef<HTMLDivElement>(null);

    const [guttersMap, setGuttersMap] = useState<TableGutterMap>({} as TableGutterMap);
    const [selectedGutter, setSelectedGutter] = useState<Maybe<TableGutter>>({} as TableGutter);
    const [selectionBounds, setSelectionBounds] = useState<Bound>();
    const [selectedCells, setSelectedCells] = useState<Annotation[]>([]);

    const gutterParams: GutterParams = {
        draggableGutterWidth: 10,
        visibleGutterWidth: 2
    };
    const [scaledCells, setScaledCells] = useState<Annotation[]>(annotation.tableCells ?? []);

    useEffect(() => {
        if (scaledCells.length) {
            const newGutters = recalculatePartsBasedOnCells(
                annotation,
                guttersMap,
                gutterParams,
                scaledCells
            );
            setGuttersMap(newGutters);
            setIsNeedToSaveTable({
                gutters: newGutters,
                cells: scaledCells
            });
        }
    }, [scaledCells]);
    useEffect(() => {
        let newGutters = createInitialGutters(
            tableModeRows,
            tableModeColumns,
            annotation,
            selectedAnnotation,
            gutterParams
        );

        // TODO: Placeholders if initial structure of table is corrupted
        const initialCells = createInitialCells(
            tableModeRows,
            tableModeColumns,
            annotation,
            selectedAnnotation
        );
        setScaledCells(initialCells);
        if (initialCells.length) {
            newGutters = recalculatePartsBasedOnCells(
                annotation,
                newGutters,
                gutterParams,
                initialCells
            );
        } else {
            newGutters = recalculatePartsBasedOnCells(
                annotation,
                newGutters,
                gutterParams,
                annotation.tableCells!
            );
        }

        setGuttersMap(newGutters);
        setIsNeedToSaveTable({ gutters: newGutters, cells: initialCells });
    }, [tableModeRows, tableModeColumns, selectedAnnotation]);

    const onMouseDownOnGutter = useGutterClick(
        panoRef,
        annotation,
        selectedAnnotation,
        guttersMap,
        scale,
        setSelectedGutter
    );

    const onMouseUpHandler = () => {
        setSelectedGutter(undefined);
        setIsNeedToSaveTable({
            gutters: guttersMap,
            cells: scaledCells
        });
    };

    const onGuttersChanged = (newGutters: TableGutterMap) => {
        setGuttersMap(newGutters);
        setIsNeedToSaveTable({
            gutters: newGutters,
            cells: scaledCells
        });
    };

    const onScaledCellsChanged = (newCells: Annotation[]) => {
        setScaledCells(newCells);
        setIsNeedToSaveTable({
            gutters: guttersMap,
            cells: newCells
        });
    };

    const onSelectedBoundsChanged = (newBound: Bound) => {
        setSelectionBounds(newBound);
    };

    const onSelectedCellsChanged = (newCells: Annotation[]) => {
        setSelectedCells(newCells);
    };

    useGutterMove({
        panoRef: panoRef,
        selectedGutter: selectedGutter,
        annotation: annotation,
        selectedAnnotation: selectedAnnotation,
        gutters: guttersMap,
        onGuttersChanged,
        isCellMode,
        onMouseUpHandler,
        scaledCells,
        onScaledCellsChanged
    });

    useCellSelection({
        selectedAnnotation: selectedAnnotation,
        annotation: annotation,
        gutters: guttersMap,
        isCellMode: isCellMode,
        panoRef: panoRef,
        onSelectedBoundsChanged,
        scaledCells,
        onSelectedCellsChanged
    });

    useEffect(() => {
        if (!isCellMode) {
            setSelectionBounds(undefined);
            setSelectedCellsCanBeMerged(false);
            setSelectedCellsCanBeSplitted(false);
            setTableCellCategory('');
            setCellsSelected(false);
        }
    }, [isCellMode]);

    useEffect(() => {
        if (selectionBounds && Object.values(selectionBounds).length > 0) {
            setCellsSelected(true);
            const canMerged = canMergeSelectedCells(selectedCells, selectionBounds);
            const canSplitted = canSplitSelectedCells(selectedCells, selectionBounds);
            setSelectedCellsCanBeMerged(canMerged);
            setSelectedCellsCanBeSplitted(canSplitted);
        } else setTableCellCategory('');
    }, [selectionBounds]);

    useEffect(() => {
        if (
            selectionBounds &&
            isSelectionBounds(selectionBounds) &&
            isRectangularShape(selectedCells)
        ) {
            let cellCategory = selectedCells[0].category;
            for (let cell of selectedCells) {
                if (cellCategory === cell.category) continue;
                cellCategory = '';
            }
            if (cellCategory === '') {
                setTableCellCategory('');
                return;
            }
            if (cellCategory !== tableCellCategory && tableCellCategory === '')
                setTableCellCategory(cellCategory);
            else {
                const newCells = selectedCells.map((el) => ({
                    ...el,
                    category: tableCellCategory
                }));
                const restCells = scaledCells.filter(
                    (el) => !newCells.map((it) => it.id).includes(el.id)
                );
                setIsNeedToSaveTable({ gutters: guttersMap, cells: [...restCells, ...newCells] });
                setScaledCells([...restCells, ...newCells]);
            }
        }
    }, [selectionBounds, tableCellCategory]);

    const performMergeCells = () => {
        if (!selectedCells.length) return;
        const newCells = removeMergedCellsAndAddNewCell(scaledCells, selectedCells);
        if (!newCells) return;
        const newGutters = recalculatePartsBasedOnCells(
            annotation,
            guttersMap,
            gutterParams,
            newCells
        );
        setGuttersMap(newGutters);
        setScaledCells(newCells);
    };

    const performSplitCells = () => {
        if (!selectedCells.length) return;
        const newCells = splitSelectedCells(scaledCells, selectedCells, guttersMap, annotation);
        if (!newCells) return;
        const newGutters = recalculatePartsBasedOnCells(
            annotation,
            guttersMap,
            gutterParams,
            newCells
        );
        setGuttersMap(newGutters);
        setScaledCells(newCells);
    };

    useEffect(() => {
        if (mergeCells) {
            performMergeCells();
            onMergeCellsClicked(false);
            setSelectionBounds(undefined);
            setSelectedCellsCanBeMerged(false);
            setSelectedCellsCanBeSplitted(false);
            setCellsSelected(false);
        }
        if (splitCells) {
            performSplitCells();
            onSplitCellsClicked(false);
            setSelectionBounds(undefined);
            setSelectedCellsCanBeMerged(false);
            setSelectedCellsCanBeSplitted(false);
            setCellsSelected(false);
        }
    }, [mergeCells, splitCells]);

    const annStyle = {
        left: x,
        top: y,
        width: width,
        height: height,
        border: `2px ${color} solid`,
        color: color,
        zIndex: isSelected ? 10 : 1
    };

    return (
        <div
            role="none"
            onClick={!isCellMode ? onClick : () => {}}
            onDoubleClick={(e) => {
                setTableModeRows(annotation.table!.rows.length + 1);
                setTableModeColumns(annotation.table!.cols.length + 1);
                onDoubleClick(e);
            }}
            onContextMenu={onContextMenu}
            className={styles.tableAnnotation}
            style={annStyle}
            ref={tableRef}
            id={getAnnotationElementId(page, id)}
        >
            <TextLabel
                color={color}
                className={styles['tableAnnotation-label']}
                label={label}
                onCloseIconClick={onCloseIconClick}
                isEditable={isEditable}
            />
            <GuttersLayer
                gutters={guttersMap}
                selectedGutter={selectedGutter}
                onMouseDownOnGutter={onMouseDownOnGutter}
                isCellMode={isCellMode}
                color={color}
            />
            <CellSelectionLayer selectionBounds={selectionBounds} />
            <TableCellLayer
                table={annotation}
                cells={scaledCells}
                scale={scale}
                categories={categories}
            />
        </div>
    );
};
