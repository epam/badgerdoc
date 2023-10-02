// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import {
    Annotation,
    Bound,
    GutterParams,
    GutterPart,
    GutterType,
    Maybe,
    TableApi,
    TableGutter,
    TableGutterMap
} from '../../typings';

export const updateAnnotation = (
    annotation: Annotation,
    gutters: TableGutterMap,
    scale: number
): TableApi => {
    const cols: number[] = [];
    const rows: number[] = [];
    for (let gutter of Object.values(gutters)) {
        if (gutter.type === 'vertical') {
            cols.push(gutter.stablePosition.start.x / scale);
        } else {
            rows.push(gutter.stablePosition.start.y / scale);
        }
    }
    return {
        cols,
        rows
    };
};

export const isRectangularShape = (cells: Annotation[]): boolean => {
    return traverseRowsOrCols('row', cells) && traverseRowsOrCols('col', cells);
};

export const traverseRowsOrCols = (selector: 'row' | 'col', cells: Annotation[]): boolean => {
    const needToEnd = true;
    let cellIdx = 0;
    let maxOnCurDirectLine = -1;
    const spanSelector = selector + 'span';
    const reverseSelector = selector === 'row' ? 'col' : 'row';
    const reverseSpanSelector = reverseSelector + 'span';
    while (needToEnd) {
        // TODO: omg while true
        const curCell = cells[cellIdx];
        if (!curCell) {
            break;
        }
        const cellsOnDirectLine = cells
            .filter(
                (el) =>
                    el.data[selector] <= curCell.data[selector] &&
                    el.data[selector] + (el.data[spanSelector] ? el.data[spanSelector] - 1 : 0) >=
                        curCell.data[selector]
            )
            .sort((a, b) => a.data[reverseSelector] - b.data[reverseSelector]);
        const lastCell = cellsOnDirectLine[cellsOnDirectLine.length - 1];
        const firstCell = cellsOnDirectLine[0];
        if (maxOnCurDirectLine === -1) {
            maxOnCurDirectLine =
                cellsOnDirectLine.length > 0
                    ? lastCell.data[reverseSelector] +
                      (lastCell.data[reverseSpanSelector]
                          ? lastCell.data[reverseSpanSelector] - 1
                          : 0) -
                      firstCell.data[reverseSelector]
                    : firstCell.data[reverseSpanSelector]
                    ? firstCell.data[reverseSpanSelector]
                    : 1;
        }
        const newMaxOnCurDirectLine =
            cellsOnDirectLine.length > 0
                ? lastCell.data[reverseSelector] +
                  (lastCell.data[reverseSpanSelector]
                      ? lastCell.data[reverseSpanSelector] - 1
                      : 0) -
                  firstCell.data[reverseSelector]
                : firstCell.data[reverseSpanSelector]
                ? firstCell.data[reverseSpanSelector]
                : 1;
        if (newMaxOnCurDirectLine !== maxOnCurDirectLine) {
            return false;
        }
        cellIdx++;
    }
    return true;
};

export const isSelectionBounds = (selectionBounds: Bound): boolean => {
    return !!selectionBounds && Object.values(selectionBounds).length > 0;
};

export const canMergeSelectedCells = (cells: Annotation[], selectionBounds: Bound): boolean => {
    /* TODO: VERY EXPENSIVE ALGO */
    return (
        !!selectionBounds && Object.values(selectionBounds).length > 0 && isRectangularShape(cells)
    );
};

export const canSplitSelectedCells = (cells: Annotation[], selectionBounds: Bound): boolean => {
    /* TODO: VERY EXPENSIVE ALGO */
    if (!isRectangularShape(cells)) return false;
    for (let cell of cells) {
        if (cell.data.rowspan || cell.data.colspan)
            return isSelectionBounds(selectionBounds) && true;
    }
    return false;
};

export const createInitialCells = (
    rows: number | null,
    columns: number | null,
    annotation: Annotation,
    selectedAnnotation: Maybe<Annotation>
): Annotation[] => {
    if (!rows || !columns || !selectedAnnotation || selectedAnnotation.id !== annotation.id) {
        return [];
    }

    let maxRow = 0;
    let maxCol = 0;
    for (let cell of annotation.tableCells!) {
        if (cell.data.row + (cell.data.rowspan ? cell.data.rowspan - 1 : 0) > maxRow)
            maxRow = cell.data.row + (cell.data.rowspan ? cell.data.rowspan - 1 : 0);
        if (cell.data.col + (cell.data.colspan ? cell.data.colspan - 1 : 0) > maxCol)
            maxCol = cell.data.col + (cell.data.colspan ? cell.data.colspan - 1 : 0);
    }

    const needUpdateRows = rows - maxRow - 1;
    const needUpdateCols = columns - maxCol - 1;

    if (
        selectedAnnotation &&
        selectedAnnotation.tableCells &&
        selectedAnnotation.tableCells.length &&
        !needUpdateCols &&
        !needUpdateRows
    ) {
        return selectedAnnotation.tableCells;
    }

    const newCells: Annotation[] = [];
    let counter = 1;
    //TODO: WHEN REMOVING NEED TO DECREASE ROWSPAN COLSPAN
    if (needUpdateCols !== 0) {
        const delta = annotation.bound.width / columns;
        for (let cell of annotation.tableCells!) {
            let updatedCell = {
                ...cell,
                id: Date.now() + counter,
                bound: {
                    x: annotation.bound.x + delta * cell.data.col,
                    y: cell.bound.y,
                    width: delta + delta * (cell.data.colspan ? cell.data.colspan - 1 : 0),
                    height: cell.bound.height
                }
            };
            // Keep in mind that columns is bigger by 1 than max idx in 'col'
            if (
                updatedCell.data.col +
                    (updatedCell.data.colspan ? updatedCell.data.colspan - 1 : 0) <
                columns
            ) {
                newCells.push(updatedCell);
                counter++;
            }
            if (
                needUpdateCols < 0 &&
                updatedCell.data.colspan > 1 &&
                updatedCell.data.col + updatedCell.data.colspan - 1 === columns
            ) {
                updatedCell.data.colspan -= 1;
                updatedCell.bound.width =
                    annotation.bound.x + annotation.bound.width - updatedCell.bound.x;
                newCells.push(updatedCell);
                counter++;
            }
            if (
                needUpdateCols > 0 &&
                updatedCell.data.col +
                    (updatedCell.data.colspan ? updatedCell.data.colspan - 1 : 0) ===
                    columns - 2
            ) {
                const newCell: Annotation = {
                    id: Date.now() + counter,
                    bound: {
                        x: updatedCell.bound.x + updatedCell.bound.width,
                        y: updatedCell.bound.y,
                        width: delta,
                        height: updatedCell.bound.height
                    },
                    data: {
                        row: updatedCell.data.row,
                        col: updatedCell.data.col + 1,
                        rowspan: updatedCell.data.rowspan
                    },
                    boundType: 'table_cell',
                    category: 'te-cell'
                };
                newCells.push(newCell);
                counter++;
            }
        }
    }
    if (needUpdateRows !== 0) {
        const delta = annotation.bound.height / rows;
        for (let cell of annotation.tableCells!) {
            let updatedCell = {
                ...cell,
                id: Date.now() + counter,
                bound: {
                    x: cell.bound.x,
                    y: annotation.bound.y + delta * cell.data.row,
                    width: cell.bound.width,
                    height: delta + delta * (cell.data.rowspan ? cell.data.rowspan - 1 : 0)
                }
            };
            if (
                updatedCell.data.row +
                    (updatedCell.data.rowspan ? updatedCell.data.rowspan - 1 : 0) <
                rows
            ) {
                newCells.push(updatedCell);
                counter++;
            }
            if (
                needUpdateRows < 0 &&
                updatedCell.data.rowspan > 1 &&
                updatedCell.data.row + updatedCell.data.rowspan - 1 === rows
            ) {
                updatedCell.data.rowspan -= 1;
                updatedCell.bound.height =
                    annotation.bound.y + annotation.bound.height - updatedCell.bound.y;
                newCells.push(updatedCell);
                counter++;
            }
            if (
                needUpdateRows > 0 &&
                updatedCell.data.row +
                    (updatedCell.data.rowspan ? updatedCell.data.rowspan - 1 : 0) ===
                    rows - 2
            ) {
                const newCell: Annotation = {
                    id: Date.now() + counter,
                    bound: {
                        x: updatedCell.bound.x,
                        y: updatedCell.bound.y + updatedCell.bound.height,
                        width: updatedCell.bound.width,
                        height: delta
                    },
                    data: {
                        row: updatedCell.data.row + 1,
                        col: updatedCell.data.col,
                        colspan: updatedCell.data.colspan
                    },
                    boundType: 'table_cell',
                    category: 'te-cell'
                };
                newCells.push(newCell);
                counter++;
            }
        }
    }
    if (annotation.tableCells?.length === 0) {
        const newCell: Annotation = {
            id: Date.now(),
            bound: {
                x: annotation.bound.x,
                y: annotation.bound.y,
                width: annotation.bound.width,
                height: annotation.bound.height
            },
            data: {
                row: 0,
                col: 0
            },
            boundType: 'table_cell',
            category: 'te-cell'
        };
        newCells.push(newCell);
    }
    return newCells;
};

const updateTableEntity = (
    entity: number | null,
    annotation: Annotation,
    selectedAnnotation: Maybe<Annotation>,
    selector: 'rows' | 'cols'
): number[] => {
    const boundSelector: 'width' | 'height' = selector === 'cols' ? 'width' : 'height';
    let entityArray = annotation.table![selector];
    if (!selectedAnnotation || selectedAnnotation.id !== annotation.id) {
        return entityArray;
    }
    if (entity && annotation.table![selector].length !== entity - 1) {
        entityArray.length = 0;
        const offset = annotation.bound[boundSelector] / entity;
        for (let i = 0; i < entity - 1; ++i) {
            entityArray.push((i + 1) * offset);
        }
    }
    return entityArray;
};

export const createInitialGutters = (
    rows: number | null,
    columns: number | null,
    annotation: Annotation,
    selectedAnnotation: Maybe<Annotation>,
    gutterParams: GutterParams
): TableGutterMap => {
    let tableCols: number[] = updateTableEntity(columns, annotation, selectedAnnotation, 'cols');
    let tableRows: number[] = updateTableEntity(rows, annotation, selectedAnnotation, 'rows');
    const gutters: TableGutterMap = {};
    if (annotation.table && tableRows && tableCols) {
        for (let i = 0; i < tableRows.length; ++i) {
            gutters[i] = {
                id: i,
                type: 'horizontal',
                draggableGutterWidth: gutterParams.draggableGutterWidth,
                visibleGutterWidth: gutterParams.visibleGutterWidth,
                maxGap: {
                    leftBoundary: tableRows[i - 1] ?? 0,
                    rightBoundary: tableRows[i + 1] ?? annotation.bound.height
                },
                stablePosition: {
                    start: {
                        x: 0,
                        y: tableRows[i]
                    },
                    end: {
                        x: annotation.bound.width,
                        y: tableRows[i]
                    }
                },
                parts: calculateExistingParts(tableCols, annotation.bound.width)
            };
        }
        for (let j = 0; j < tableCols.length; ++j) {
            gutters[j + tableRows.length] = {
                id: j + tableRows.length,
                type: 'vertical',
                draggableGutterWidth: gutterParams.draggableGutterWidth,
                visibleGutterWidth: gutterParams.visibleGutterWidth,
                maxGap: {
                    leftBoundary: tableCols[j - 1] ?? 0,
                    rightBoundary: tableCols[j + 1] ?? annotation.bound.width
                },
                stablePosition: {
                    start: {
                        x: tableCols[j],
                        y: 0
                    },
                    end: {
                        x: tableCols[j],
                        y: annotation.bound.height
                    }
                },
                parts: calculateExistingParts(tableRows, annotation.bound.height)
            };
        }
    }
    return gutters;
};

export const sumArrToIndex = (gutter: TableGutter, idx: number): number => {
    let res = 0;
    if (gutter.type === 'vertical') {
        for (let i = 0; i < idx; ++i) {
            res += gutter.parts[i].length;
        }
    } else {
        for (let i = 0; i < idx; ++i) {
            res += gutter.parts[i].length;
        }
    }
    return res;
};

const calculateExistingParts = (array: number[], maxLength: number): GutterPart[] => {
    let prev = 0;
    return array
        .map((gutterLength) => {
            const newLength = gutterLength - prev;
            prev = gutterLength;
            return {
                length: newLength,
                visibility: true
            };
        })
        .concat([
            {
                length: maxLength - prev,
                visibility: true
            }
        ]);
};

//TODO: DO NOT REMOVE JUST YET
export const createGuttersFromAnnotation = (
    annotation: Annotation,
    gutterParams: GutterParams
): TableGutterMap => {
    const gutters: TableGutterMap = {};
    if (annotation.table && annotation.table.cols && annotation.table.rows) {
        for (let i = 0; i < annotation.table.rows.length; ++i) {
            gutters[i] = {
                id: i,
                type: 'horizontal',
                draggableGutterWidth: gutterParams.draggableGutterWidth,
                visibleGutterWidth: gutterParams.visibleGutterWidth,
                maxGap: {
                    leftBoundary: annotation.table.rows[i - 1] ?? 0,
                    rightBoundary: annotation.table.rows[i + 1] ?? annotation.bound.height
                },
                stablePosition: {
                    start: {
                        x: 0,
                        y: annotation.table.rows[i]
                    },
                    end: {
                        x: annotation.bound.width,
                        y: annotation.table.rows[i]
                    }
                },
                parts: calculateExistingParts(annotation.table.cols, annotation.bound.width)
            };
        }
        for (let j = 0; j < annotation.table.cols.length; ++j) {
            gutters[j + annotation.table.rows.length] = {
                id: j + annotation.table.rows.length,
                type: 'vertical',
                draggableGutterWidth: gutterParams.draggableGutterWidth,
                visibleGutterWidth: gutterParams.visibleGutterWidth,
                maxGap: {
                    leftBoundary: annotation.table.cols[j - 1] ?? 0,
                    rightBoundary: annotation.table.cols[j + 1] ?? annotation.bound.width
                },
                stablePosition: {
                    start: {
                        x: annotation.table.cols[j],
                        y: 0
                    },
                    end: {
                        x: annotation.table.cols[j],
                        y: annotation.bound.height
                    }
                },
                parts: calculateExistingParts(annotation.table.rows, annotation.bound.height)
            };
        }
    }
    return gutters;
};

const getGutterIdxByRelativeIdx = (
    gutters: TableGutterMap,
    idx: number,
    type: GutterType
): number => {
    for (let gutter of Object.values(gutters)) {
        if (gutter.type !== type) continue;
        if (idx === 0) return gutter.id;
        idx--;
    }
    return -1;
};

const processCellSpan = (
    cell: Annotation,
    selector: 'row' | 'col',
    gutters: TableGutterMap,
    newGutters: TableGutterMap
) => {
    const cellSpan: 'colspan' | 'rowspan' = `${selector}span`;
    const reverseSelector: 'col' | 'row' = selector === 'row' ? 'col' : 'row';
    const reverseCellSpan: 'colspan' | 'rowspan' = `${reverseSelector}span`;
    const gutterType: GutterType = selector === 'row' ? 'horizontal' : 'vertical';
    if (cell.data[cellSpan] > 1) {
        const affectedGutterIdx = getGutterIdxByRelativeIdx(
            gutters,
            cell.data[selector],
            gutterType
        );
        if (affectedGutterIdx < 0) return;
        for (let i = 0; i < cell.data[cellSpan] - 1; ++i) {
            if (cell.data[reverseCellSpan] >= 2) {
                for (let j = 0; j < cell.data[reverseCellSpan]; ++j) {
                    newGutters[affectedGutterIdx + i].parts[
                        cell?.data[reverseSelector] + j
                    ].visibility = false;
                }
            } else {
                newGutters[affectedGutterIdx + i].parts[cell?.data[reverseSelector]].visibility =
                    false;
            }
        }
    }
};

const processCellWithoutSpans = (
    cell: Annotation,
    gutters: TableGutterMap,
    newGutters: TableGutterMap
) => {
    const affectedGutterIdxCol = getGutterIdxByRelativeIdx(gutters, cell.data.col, 'vertical');
    const affectedGutterIdxRow = getGutterIdxByRelativeIdx(gutters, cell.data.row, 'horizontal');
    if (affectedGutterIdxCol >= 0) {
        newGutters[affectedGutterIdxCol].parts[cell.data.row].visibility = true;
    }
    if (affectedGutterIdxRow >= 0) {
        newGutters[affectedGutterIdxRow].parts[cell.data.col].visibility = true;
    }
};

export const recalculatePartsBasedOnCells = (
    annotation: Annotation,
    gutters: TableGutterMap,
    gutterParams: GutterParams,
    scaledCells: Annotation[]
): TableGutterMap => {
    const newGutters: TableGutterMap = gutters;
    for (let cell of scaledCells) {
        if (!cell.data.rowspan && !cell.data.colspan) {
            processCellWithoutSpans(cell, gutters, newGutters);
            continue;
        }
        processCellSpan(cell, 'row', gutters, newGutters);
        processCellSpan(cell, 'col', gutters, newGutters);
    }
    return newGutters;
};

export const getLastCell = (selectedCells: Annotation[]): Maybe<Annotation> => {
    let maxRow = 0;
    const cellsWithMaxRow = [];
    for (let cell of selectedCells) {
        if (cell.data.row + (cell.data.rowspan ? cell.data.rowspan - 1 : 0) > maxRow) {
            cellsWithMaxRow.length = 0;
            maxRow = cell.data.row + (cell.data.rowspan ? cell.data.rowspan - 1 : 0);
            cellsWithMaxRow.push(cell);
        } else if (cell.data.row + (cell.data.rowspan ? cell.data.rowspan - 1 : 0) === maxRow) {
            cellsWithMaxRow.push(cell);
        }
    }
    let maxCell: Maybe<Annotation>;
    let maxCol = 0;
    for (let cell of cellsWithMaxRow) {
        if (cell.data.col + (cell.data.colspan ? cell.data.colspan - 1 : 0) > maxCol) {
            maxCol = cell.data.col + (cell.data.colspan ? cell.data.colspan - 1 : 0);
            maxCell = cell;
        } else if (cellsWithMaxRow.length === 1) maxCell = cell;
    }
    return maxCell;
};

export const calculateSpanByCells = (
    cell1: Annotation,
    cell2: Annotation,
    selector: 'row' | 'col'
): number => {
    if (cell1.data[selector] === cell2.data[selector]) {
        return Math.max(cell2.data[`${selector}span`] ?? 0, cell1.data[`${selector}span`] ?? 0);
    }
    return (
        cell2.data[selector] +
        (cell2.data[`${selector}span`] ? cell2.data[`${selector}span`] : 1) -
        cell1.data[selector]
    );
};

export const getFirstCell = (selectedCells: Annotation[]): Maybe<Annotation> => {
    let minRow = Number.MAX_SAFE_INTEGER;
    const cellsWithMinRow = [];
    for (let cell of selectedCells) {
        if (cell.data.row < minRow) {
            cellsWithMinRow.length = 0;
            minRow = cell.data.row;
            cellsWithMinRow.push(cell);
        } else if (cell.data.row === minRow) {
            cellsWithMinRow.push(cell);
        }
    }
    let minCell: Maybe<Annotation>;
    let minCol = Number.MAX_SAFE_INTEGER;
    for (let cell of cellsWithMinRow) {
        if (cell.data.col < minCol) {
            minCol = cell.data.col;
            minCell = cell;
        } else if (cellsWithMinRow.length === 1) minCell = cell;
    }
    return minCell;
};

export const removeMergedCellsAndAddNewCell = (
    scaledCells: Annotation[],
    selectedCells: Annotation[]
): Maybe<Annotation[]> => {
    const firstCell = getFirstCell(selectedCells);
    const lastCell = getLastCell(selectedCells);
    if (!lastCell || !firstCell) return undefined;
    const rowspan = calculateSpanByCells(firstCell, lastCell, 'row');
    const colspan = calculateSpanByCells(firstCell, lastCell, 'col');
    const newData = {
        row: firstCell.data.row,
        col: firstCell.data.col,
        rowspan,
        colspan
    };
    return scaledCells
        .filter((x) => !selectedCells.map((el) => el.id).includes(x.id))
        .concat({
            ...firstCell,
            bound: {
                x: firstCell.bound.x,
                y: firstCell.bound.y,
                height: lastCell.bound.y - firstCell.bound.y + lastCell.bound.height,
                width: lastCell.bound.x - firstCell.bound.x + lastCell.bound.width
            },
            data: newData
        });
};

const splitByCols = (
    cell: Annotation,
    gutters: TableGutterMap,
    annotation: Annotation
): Annotation[] => {
    if (!cell.data.colspan) return [cell];
    const newCells: Annotation[] = [];
    for (let i = 0; i < cell.data.colspan; ++i) {
        const nextGutterIdx = getGutterIdxByRelativeIdx(gutters, cell.data.col + i, 'vertical');
        const prevGutterIdx = getGutterIdxByRelativeIdx(gutters, cell.data.col + i - 1, 'vertical');
        const leftBorder =
            prevGutterIdx >= 0
                ? annotation.bound.x + gutters[prevGutterIdx].stablePosition.start.x
                : annotation.bound.x;
        const rightBorder =
            nextGutterIdx >= 0
                ? annotation.bound.x + gutters[nextGutterIdx].stablePosition.start.x
                : annotation.bound.x + annotation.bound.width;
        const newCell: Annotation = {
            id: Date.now() + i,
            bound: {
                x: leftBorder,
                y: cell.bound.y,
                width: rightBorder - leftBorder,
                height: cell.bound.height
            },
            data: {
                row: cell.data.row,
                col: cell.data.col + i,
                rowspan: cell.data.rowspan,
                colspan: 0
            },
            boundType: 'table_cell',
            category: 'te-cell'
        };
        newCells.push(newCell);
    }
    return newCells;
};

const splitByRows = (
    cell: Annotation,
    gutters: TableGutterMap,
    annotation: Annotation,
    idCounter: number
): Annotation[] => {
    if (!cell.data.rowspan) return [cell];
    const newCells: Annotation[] = [];
    for (let i = 0; i < cell.data.rowspan; ++i) {
        const nextGutterIdx = getGutterIdxByRelativeIdx(gutters, cell.data.row + i, 'horizontal');
        const prevGutterIdx = getGutterIdxByRelativeIdx(
            gutters,
            cell.data.row + i - 1,
            'horizontal'
        );
        const leftBorder =
            prevGutterIdx >= 0
                ? annotation.bound.y + gutters[prevGutterIdx].stablePosition.start.y
                : annotation.bound.y;
        const rightBorder =
            nextGutterIdx >= 0
                ? annotation.bound.y + gutters[nextGutterIdx].stablePosition.start.y
                : annotation.bound.y + annotation.bound.height;
        const newCell: Annotation = {
            id: Date.now() + i + idCounter,
            bound: {
                x: cell.bound.x,
                y: leftBorder,
                width: cell.bound.width,
                height: rightBorder - leftBorder
            },
            data: {
                row: cell.data.row + i,
                col: cell.data.col,
                rowspan: 0,
                colspan: cell.data.colspan
            },
            boundType: 'table_cell',
            category: 'te-cell'
        };
        newCells.push(newCell);
    }
    return newCells;
};

export const splitSelectedCells = (
    scaledCells: Annotation[],
    selectedCells: Annotation[],
    gutters: TableGutterMap,
    annotation: Annotation
): Maybe<Annotation[]> => {
    const restCells = scaledCells.filter((x) => !selectedCells.map((el) => el.id).includes(x.id));
    const newCells: Annotation[] = [];
    let idCounter = 0;
    for (let cell of selectedCells) {
        if (!cell.data.rowspan && !cell.data.colspan) {
            newCells.push(cell);
            idCounter++;
            continue;
        }

        const splitted = splitByCols(cell, gutters, annotation);
        idCounter += splitted.length + 2;
        const resSplitted = [];
        for (let splittedCell of splitted) {
            const splittedByRows = splitByRows(splittedCell, gutters, annotation, idCounter);
            resSplitted.push(...splittedByRows);
            idCounter += splittedByRows.length + splitted.length;
        }
        newCells.push(...resSplitted);
    }
    return [...restCells, ...newCells];
};

export const getGutterLeft = (gutter: TableGutter): string => {
    return (
        gutter.stablePosition.start.x -
        (gutter.type === 'vertical' ? gutter.draggableGutterWidth / 2 : 0) +
        'px'
    );
};

export const getGutterTop = (gutter: TableGutter): string => {
    return (
        gutter.stablePosition.start.y -
        (gutter.type === 'horizontal' ? gutter.draggableGutterWidth / 2 : 0) +
        'px'
    );
};

export const transformInitialCells = (
    annotation: Maybe<Annotation>,
    cells: Maybe<Annotation[]>
): Annotation[] => {
    if (!annotation || !cells) {
        return [];
    }
    return cells;
};
