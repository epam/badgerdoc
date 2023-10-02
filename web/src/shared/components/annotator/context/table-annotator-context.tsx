// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { createContext, FC, useMemo, useContext, useState } from 'react';

type TableContextValue = {
    tableMode: boolean;
    tableModeColumns: number | null;
    tableModeRows: number | null;
    setTableModeColumns: (s: number) => void;
    setTableModeRows: (s: number) => void;
    isCellMode: boolean;
    setIsCellMode: (b: boolean) => void;

    cellsSelected: boolean;
    setCellsSelected: (b: boolean) => void;
    mergeCells: boolean;
    onMergeCellsClicked: (b: boolean) => void;
    selectedCellsCanBeMerged: boolean;
    setSelectedCellsCanBeMerged: (b: boolean) => void;

    splitCells: boolean;
    onSplitCellsClicked: (b: boolean) => void;
    selectedCellsCanBeSplitted: boolean;
    setSelectedCellsCanBeSplitted: (b: boolean) => void;
};

const TableAnnotatorContext = createContext<TableContextValue | undefined>(undefined);

type ProviderProps = {};

export const TableAnnotatorContextProvider: FC<ProviderProps> = ({ children }) => {
    // todo: consider removal tableMode
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [tableMode, setTableMode] = useState<boolean>(false);
    const [tableModeRows, setTableModeRows] = useState<number | null>(1);
    const [tableModeColumns, setTableModeColumns] = useState<number | null>(1);
    const [isCellMode, setIsCellMode] = useState<boolean>(false);

    const [cellsSelected, setCellsSelected] = useState<boolean>(false);
    const [mergeCells, onMergeCellsClicked] = useState<boolean>(false);
    const [selectedCellsCanBeMerged, setSelectedCellsCanBeMerged] = useState<boolean>(false);

    const [splitCells, onSplitCellsClicked] = useState<boolean>(false);
    const [selectedCellsCanBeSplitted, setSelectedCellsCanBeSplitted] = useState<boolean>(false);

    const value = useMemo<TableContextValue>(() => {
        return {
            tableMode,
            tableModeColumns,
            tableModeRows,
            setTableModeColumns,
            setTableModeRows,
            isCellMode,
            setIsCellMode,
            cellsSelected,
            setCellsSelected,
            mergeCells,
            onMergeCellsClicked,
            selectedCellsCanBeMerged,
            setSelectedCellsCanBeMerged,
            splitCells,
            onSplitCellsClicked,
            selectedCellsCanBeSplitted,
            setSelectedCellsCanBeSplitted
        };
    }, [
        tableMode,
        tableModeColumns,
        tableModeRows,
        isCellMode,
        mergeCells,
        cellsSelected,
        selectedCellsCanBeMerged,
        splitCells,
        selectedCellsCanBeSplitted
    ]);

    return (
        <TableAnnotatorContext.Provider value={value}>{children}</TableAnnotatorContext.Provider>
    );
};

export const useTableAnnotatorContext = () => {
    const context = useContext(TableAnnotatorContext);

    if (context === undefined) {
        throw new Error(
            `useTableAnnotatorContext must be used within a TableAnnotatorContextProvider`
        );
    }
    return context;
};
