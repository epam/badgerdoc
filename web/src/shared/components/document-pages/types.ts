import { ReactNode } from 'react';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { PDFPageProxy, DocumentProps } from 'react-pdf';
import { Annotation } from 'shared';
import { GridVariants } from 'shared/constants/task';

type RenderLinksParams = {
    updLinks: boolean;
    scale: number;
    annotations?: Record<number, Annotation[]>;
};

export interface PageSize {
    width: number;
    height: number;
}

export type DocumentPagesProps = {
    renderLinks?: (params: RenderLinksParams) => ReactNode;
    pageNumbers?: number[];
    fileMetaInfo: FileMetaInfo;
    apiPageSize?: PageSize;
    additionalScale: number;
    goToPage?: number;
    setPageSize?: (nS: any) => void;
    editable: boolean;
    gridVariant: GridVariants;
};

export type PageLoadedCallback = (page: PDFPageProxy | HTMLImageElement) => void;

// there is no PDFDocumentProxy exported by react-pdf, extracting it manually from
// DocumentProps
export type DocumentLoadedCallback = Required<DocumentProps>['onLoadSuccess'];
