import { CSSProperties } from 'react';
import { DocumentLoadedCallback, PageSize } from '../../types';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';

export type DocumentPDFProps = {
    pageNumbers: number[];
    handleDocumentLoaded: DocumentLoadedCallback;
    fileMetaInfo: FileMetaInfo;
    pageSize?: PageSize;
    editable: boolean;
    fullScale: number;
    containerRef: {
        current: HTMLDivElement | null;
    };
};

export type ListItemData = Pick<
    DocumentPDFProps,
    'pageNumbers' | 'fullScale' | 'pageSize' | 'containerRef' | 'editable'
>;

export type PDFPageRendererProps = {
    data: ListItemData;
    index: number;
    style: CSSProperties;
};

export type TDocumentPDFRef = {
    scrollDocumentTo(index: number): void;
};
