import { IconButton, IconContainer, Spinner } from '@epam/loveship';
import { ReactComponent as increaseIcon } from '@epam/assets/icons/common/action-add-24.svg';
import { ReactComponent as decreaseIcon } from '@epam/assets/icons/common/content-minus-24.svg';
import { ReactComponent as searchIcon } from '@epam/assets/icons/common/action-search-18.svg';
// import { ReactComponent as squareIcon } from '@epam/assets/icons/common/action-copy_content-18.svg';
import React, { CSSProperties, FC, Fragment, ReactNode, useEffect, useState } from 'react';
import { Document, Page, PDFPageProxy, pdfjs } from 'react-pdf';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { Image } from '../image/image';

import styles from './document-pages.module.scss';
import './react-pdf.scss';
import DocumentSinglePage from './document-single-page';
import { Annotation } from 'shared';

export interface PageSize {
    width: number;
    height: number;
}

type DocumentPagesProps = {
    renderLinks?: (params: RenderLinksParams) => ReactNode;
    pageNumbers?: number[];
    fileMetaInfo: FileMetaInfo;
    apiPageSize?: PageSize;
    setPageSize?: (nS: any) => void;
    annotatorLinks: Record<number, Annotation[]>;
    containerRef: React.RefObject<HTMLDivElement>;
    scaleStyle?: CSSProperties;

    editable: boolean;
    onAnnotationCopyPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationCutPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationPastePress: (pageSize: PageSize, pageNum: number) => void;
    onAnnotationUndoPress: () => void;
    onAnnotationRedoPress: () => void;
    onEmptyAreaClick: () => void;
};

export const getScale = (
    containerWidth: number,
    contentWidth: number,
    containerPadding: number = 0
) => {
    // need to limit fraction part to get rid of loss of precision when return to initial zoom
    const highAccuracyScale = (containerWidth - containerPadding) / contentWidth;
    return Math.round(highAccuracyScale * 1000) / 1000;
};

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const DocumentPages: FC<DocumentPagesProps> = ({
    pageNumbers = [],
    fileMetaInfo,
    apiPageSize,
    setPageSize,
    scaleStyle,
    renderLinks,
    annotatorLinks,
    containerRef,
    editable,
    onAnnotationCopyPress,
    onAnnotationCutPress,
    onAnnotationPastePress,
    onAnnotationUndoPress,
    onAnnotationRedoPress,
    onEmptyAreaClick
}) => {
    const [scale, setScale] = useState(0);
    const [initialScale, setInitialScale] = useState(0);
    const [originalPageSize, setOriginalPageSize] = useState<PageSize>();

    const [updLinks, setUpdLinks] = useState<boolean>(false);

    const [readyLinks, setReadyLinks] = useState(null as ReactNode);

    useEffect(() => {
        const newPageSize = apiPageSize && apiPageSize.height > 0 ? apiPageSize : originalPageSize;
        setPageSize!(newPageSize);
    }, [apiPageSize, originalPageSize]);

    useEffect(() => {
        if (!containerRef.current || !apiPageSize || !apiPageSize.width) return;

        containerRef.current.style.overflow = 'scroll';
        const width = containerRef.current.clientWidth;
        containerRef.current.style.overflow = '';

        const newScale = getScale(width, apiPageSize.width, 20);
        setScale(newScale);
        setInitialScale(newScale);
    }, [apiPageSize]);
    const handlePageLoaded = (page: PDFPageProxy | HTMLImageElement) => {
        if (!originalPageSize) {
            if ('originalWidth' in page) {
                setOriginalPageSize({ width: page.originalWidth, height: page.originalHeight });
            } else {
                setOriginalPageSize({ width: page.naturalWidth, height: page.naturalHeight });
            }
        }
    };

    const pageScale = (
        <div className={styles['page-scale']} style={scaleStyle}>
            <div className={styles['page-scale__button-group']}>
                <button
                    className={`${styles['page-scale__item']} ${
                        scale > initialScale ? styles['page-scale__item--active'] : ''
                    }`}
                    onClick={() => setScale(scale + 0.1)}
                >
                    <IconButton icon={increaseIcon} />
                </button>
                <div>
                    <IconContainer icon={searchIcon} />
                </div>
                <button
                    className={`${styles['page-scale__item']} ${
                        scale < initialScale ? styles['page-scale__item--active'] : ''
                    }`}
                    onClick={() => setScale(scale - 0.1)}
                >
                    <IconButton icon={decreaseIcon} />
                </button>
            </div>
            {/*will be active in future*/}
            {/*<div className={styles['page-scale__button-group']}>*/}
            {/*    <button className={styles['page-scale__item']} onClick={() => {}}>*/}
            {/*        <IconButton icon={squareIcon} />*/}
            {/*    </button>*/}
            {/*</div>*/}
        </div>
    );

    const handleLinksUpdate = () => {
        setUpdLinks((prev) => !prev);
    };

    useEffect(() => {
        const links = renderLinks!({ scale, updLinks });
        setReadyLinks(links);
    }, [updLinks, scale, annotatorLinks]);

    return (
        <div className={styles['pdf-container']}>
            {pageScale}
            <div className={`${styles['pdf-parent']} pdf-parent`}>
                {fileMetaInfo.extension === '.pdf' ? (
                    <>
                        <Document
                            file={getPdfDocumentAddress(fileMetaInfo.id)}
                            loading={<Spinner color="sky" />}
                            options={{ httpHeaders: getAuthHeaders() }}
                            className={styles['document-wrapper']}
                        >
                            {pageNumbers.map((pageNum) => {
                                return (
                                    <Fragment key={pageNum}>
                                        <DocumentSinglePage
                                            scale={scale}
                                            pageSize={apiPageSize}
                                            pageNum={pageNum}
                                            handlePageLoaded={handlePageLoaded}
                                            handleLinksUpdate={handleLinksUpdate}
                                            containerRef={containerRef}
                                            editable={editable}
                                            onAnnotationCopyPress={onAnnotationCopyPress}
                                            onAnnotationCutPress={onAnnotationCutPress}
                                            onAnnotationPastePress={onAnnotationPastePress}
                                            onAnnotationUndoPress={onAnnotationUndoPress}
                                            onAnnotationRedoPress={onAnnotationRedoPress}
                                            onEmptyAreaClick={onEmptyAreaClick}
                                        />
                                    </Fragment>
                                );
                            })}
                            {<Fragment>{readyLinks}</Fragment>}
                        </Document>
                    </>
                ) : null}
                {fileMetaInfo.extension === '.jpg' ? (
                    <>
                        {pageNumbers.map((pageNum) => {
                            return (
                                <Fragment key={pageNum}>
                                    <DocumentSinglePage
                                        scale={scale}
                                        pageSize={apiPageSize}
                                        pageNum={pageNum}
                                        handlePageLoaded={handlePageLoaded}
                                        handleLinksUpdate={handleLinksUpdate}
                                        containerRef={containerRef}
                                        editable={editable}
                                        isImage
                                        imageId={fileMetaInfo.id}
                                        onAnnotationCopyPress={onAnnotationCopyPress}
                                        onAnnotationCutPress={onAnnotationCutPress}
                                        onAnnotationPastePress={onAnnotationPastePress}
                                        onAnnotationUndoPress={onAnnotationUndoPress}
                                        onAnnotationRedoPress={onAnnotationRedoPress}
                                        onEmptyAreaClick={onEmptyAreaClick}
                                    />
                                </Fragment>
                            );
                        })}
                    </>
                ) : null}
            </div>
        </div>
    );
};

export type RenderPageParams = {
    scale: number;
    pageNum: number;
    handlePageLoaded: (page: PDFPageProxy | HTMLImageElement) => void;
    pageSize?: PageSize;
    handleLinksUpdate: () => void;
    isImage?: boolean;
    imageId?: number;
};

type RenderLinksParams = {
    updLinks: boolean;
    scale: number;
};

export const defaultRenderPage = ({
    scale,
    pageNum,
    handlePageLoaded,
    pageSize,
    isImage = false,
    imageId
}: RenderPageParams) => {
    if (isImage) {
        return <Image id={imageId || 0} handlePageLoaded={handlePageLoaded} />;
    }
    return (
        <Page
            scale={scale}
            pageNumber={pageNum}
            onLoadSuccess={handlePageLoaded}
            renderAnnotationLayer={false}
            width={pageSize?.width}
            height={pageSize?.height}
        />
    );
};

export default DocumentPages;
