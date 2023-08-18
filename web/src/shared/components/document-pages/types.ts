import { PDFPageProxy } from 'react-pdf';

export type PageLoadedCallback = (page: PDFPageProxy | HTMLImageElement) => void;
