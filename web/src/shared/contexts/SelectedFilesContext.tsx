import React, { createContext, useContext, useState, useCallback } from 'react';
import { noop } from 'lodash';

interface SelectedFilesContextType {
    selectedFiles: number[];
    setSelectedFiles: (files: number[]) => void;
    toggleFile: (fileId: number) => void;
    selectAll: (fileIds: number[]) => void;
    clearSelection: () => void;
}

export const SelectedFilesContext = createContext<SelectedFilesContextType>({
    selectedFiles: [],
    setSelectedFiles: noop,
    toggleFile: noop,
    selectAll: noop,
    clearSelection: noop
});

export const SelectedFilesProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

    const toggleFile = useCallback((fileId: number) => {
        setSelectedFiles((prev) =>
            prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
        );
    }, []);

    const selectAll = useCallback((fileIds: number[]) => {
        setSelectedFiles(fileIds);
    }, []);

    const clearSelection = useCallback(() => {
        setSelectedFiles([]);
    }, []);

    const value: SelectedFilesContextType = {
        selectedFiles,
        setSelectedFiles,
        toggleFile,
        selectAll,
        clearSelection
    };

    return <SelectedFilesContext.Provider value={value}>{children}</SelectedFilesContext.Provider>;
};

export const useSelectedFiles = () => useContext(SelectedFilesContext);
