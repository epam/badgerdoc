import { ReactComponent as increaseIcon } from '@epam/assets/icons/common/action-add-24.svg';
import { ReactComponent as searchIcon } from '@epam/assets/icons/common/action-search-18.svg';
import { ReactComponent as decreaseIcon } from '@epam/assets/icons/common/content-minus-24.svg';
import { IconButton, IconContainer, Spinner } from '@epam/loveship';
import cn from 'classnames';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { Render } from 'ketcher-core';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import React, { CSSProperties, Fragment, ReactNode, useEffect, useRef, useState } from 'react';
import { Document, Page, pdfjs, PDFPageProxy } from 'react-pdf';
import { Annotation } from 'shared';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import { LinkAnnotation } from '../annotator/components/link-annotation';
import { getPointsForLinks } from '../annotator/utils/get-points-for-link';
import { Image } from '../image/image';
import styles from './document-pages.module.scss';
import DocumentSinglePage from './document-single-page';
import './react-pdf.scss';

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

const DocumentPages: React.FC<DocumentPagesProps> = ({
    pageNumbers = [],
    fileMetaInfo,
    apiPageSize,
    setPageSize,
    scaleStyle,
    editable,
    onAnnotationCopyPress,
    onAnnotationCutPress,
    onAnnotationPastePress,
    onAnnotationUndoPress,
    onAnnotationRedoPress,
    onEmptyAreaClick
}) => {
    const {
        SyncedContainer,
        annotationsByUserId,
        currentPage,
        isSplitValidation,
        onSplitAnnotationSelected,
        userPages
    } = useTaskAnnotatorContext();

    const containerRef = useRef<HTMLDivElement>(null);

    const [scale, setScale] = useState(0);
    const [initialScale, setInitialScale] = useState(0);
    const [originalPageSize, setOriginalPageSize] = useState<PageSize>();

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
        </div>
    );

    return (
        <div className={styles['pdf-container']}>
            {pageScale}
            <div ref={containerRef} className={styles['pdf-document-container']}>
                {isSplitValidation ? (
                    <Document
                        file={getPdfDocumentAddress(fileMetaInfo.id)}
                        loading={<Spinner color="sky" />}
                        options={{ httpHeaders: getAuthHeaders() }}
                        className={cn(
                            styles['split-document-wrapper'],
                            styles[`split-document-wrapper--pages-${userPages.length + 1}`]
                        )}
                    >
                        <SyncedContainer className={styles['split-document-page']}>
                            <DocumentSinglePage
                                scale={scale}
                                pageSize={apiPageSize}
                                pageNum={currentPage}
                                handlePageLoaded={handlePageLoaded}
                                containerRef={containerRef}
                                editable
                                onAnnotationCopyPress={onAnnotationCopyPress}
                                onAnnotationCutPress={onAnnotationCutPress}
                                onAnnotationPastePress={onAnnotationPastePress}
                                onAnnotationUndoPress={onAnnotationUndoPress}
                                onAnnotationRedoPress={onAnnotationRedoPress}
                                onEmptyAreaClick={onEmptyAreaClick}
                            />
                        </SyncedContainer>
                        {userPages.map((userPage) => (
                            <SyncedContainer
                                key={userPage.user_id}
                                className={styles['split-document-page']}
                            >
                                <DocumentSinglePage
                                    annotations={annotationsByUserId[userPage.user_id]}
                                    scale={scale}
                                    pageSize={apiPageSize}
                                    pageNum={userPage.page_num}
                                    onAnnotationSelected={(scaledAnn?: Annotation) =>
                                        onSplitAnnotationSelected(
                                            scale,
                                            userPage.user_id,
                                            scaledAnn
                                        )
                                    }
                                />
                            </SyncedContainer>
                        ))}
                    </Document>
                ) : (
                    <div className={`${styles['pdf-parent']} pdf-parent`}>
                        {fileMetaInfo.extension === '.pdf' ? (
                            <>
                                <Document
                                    file={getPdfDocumentAddress(fileMetaInfo.id)}
                                    loading={
                                        <div className="flex-cell">
                                            <Spinner color="sky" />
                                        </div>
                                    }
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
                )}
            </div>
        </div>
    );
};

export type RenderPageParams = {
    scale: number;
    pageNum: number;
    handlePageLoaded: (page: PDFPageProxy | HTMLImageElement) => void;
    pageSize?: PageSize;
    isImage?: boolean;
    imageId?: number;
};

type RenderLinksParams = {
    updLinks: boolean;
    scale: number;
    annotations?: Record<number, Annotation[]>;
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
