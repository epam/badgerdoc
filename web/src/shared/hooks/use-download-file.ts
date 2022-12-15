import React, { useRef, useState } from 'react';

interface DownloadFileProps {
    readonly preDownloading: () => void;
    readonly postDownloading: () => void;
    readonly onError: () => void;
}

interface DownloadedFileInfo {
    readonly download: (data: Promise<Blob>, fileName: string) => Promise<void>;
    readonly ref: React.MutableRefObject<HTMLAnchorElement | null>;
    readonly name: string | undefined;
    readonly url: string | undefined;
}

export const useDownloadFile = ({
    preDownloading,
    postDownloading,
    onError
}: DownloadFileProps): DownloadedFileInfo => {
    const ref = useRef<HTMLAnchorElement | null>(null);
    const [url, setFileUrl] = useState<string>();
    const [name, setFileName] = useState<string>();

    const download = async (data: Promise<Blob>, fileName: string) => {
        try {
            preDownloading();
            const result = await data;
            const url = URL.createObjectURL(new Blob([result]));
            setFileUrl(url);
            setFileName(fileName);
            ref.current?.click();
            postDownloading();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.log('The error occured: ', error);
            onError();
        }
    };

    return { download, ref, url, name };
};
