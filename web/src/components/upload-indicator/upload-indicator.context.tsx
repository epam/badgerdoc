import { FC, createContext, useMemo, useState } from 'react';

export type OnProgressCallback = (progress: number) => void;

export interface UploadIndicatorContextType {
    progress: number;
    setProgress: OnProgressCallback;
    isUploaded: boolean;
    resetUploadProgressState: () => void;
}

const defaultValue: UploadIndicatorContextType = {
    progress: 0,
    setProgress: () => {},
    isUploaded: false,
    resetUploadProgressState: () => {}
};

export const UploadIndicatorContext = createContext<UploadIndicatorContextType>(defaultValue);

export const UploadIndicatorContextProvider: FC = ({ children }) => {
    const [progress, setProgress] = useState<number>(0);

    const isUploaded = progress === 100;

    const resetUploadProgressState = () => {
        setProgress(0);
    };

    const contextValue: UploadIndicatorContextType = useMemo(
        () => ({
            progress,
            setProgress,
            isUploaded,
            resetUploadProgressState
        }),
        [progress, isUploaded]
    );

    return (
        <UploadIndicatorContext.Provider value={contextValue}>
            {children}
        </UploadIndicatorContext.Provider>
    );
};
