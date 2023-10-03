// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { Fragment, useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { Document, Page, pdfjs, PDFPageProxy } from 'react-pdf';
import { Annotation } from 'shared';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import { Image } from '../image/image';
import DocumentSinglePage from './document-single-page';
import { Spinner } from '@epam/loveship';
import { SplitAnnotatorInfo } from 'components/split-annotator-info';
import styles from './document-pages.module.scss';
import cn from 'classnames';
import './react-pdf.scss';
import ResizableSyncedContainer from './components/ResizableSyncedContainer';
import { cx } from '@epam/uui';
import { ValidationType } from 'api/typings';
import { GridVariants } from 'shared/constants/task';
import DocumentPDF from './components/document-pdf';
import { PageLoadedCallback, DocumentPagesProps, PageSize, DocumentLoadedCallback } from './types';

export type { PageSize } from './types';

export const getScale = (containerWidth: number, contentWidth: number) => {
    // need to limit fraction part to get rid of loss of precision when return to initial zoom
    return Math.round((containerWidth / contentWidth) * 1000) / 1000;
};

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const DocumentPages: React.FC<DocumentPagesProps> = ({
    pageNumbers = [],
    fileMetaInfo,
    apiPageSize,
    setPageSize,
    editable,
    gridVariant,
    additionalScale,
    documentPDFRef
}) => {
    const {
        SyncedContainer,
        isSplitValidation,
        onSplitAnnotationSelected,
        latestRevisionByAnnotators,
        latestRevisionByAnnotatorsWithBounds,
        currentPage,
        currentOrderPageNumber,
        selectedRelatedDoc,
        job,
        onEmptyAreaClick,
        onAnnotationCopyPress,
        onAnnotationCutPress,
        onAnnotationPastePress,
        onAnnotationUndoPress,
        onAnnotationRedoPress
    } = useTaskAnnotatorContext();
    const containerRef = useRef<HTMLDivElement>(null);

    const [scale, setScale] = useState(0);
    const [originalPageSize, setOriginalPageSize] = useState<PageSize>();

    const getAnnotatorName = useCallback(
        (annotatorId: string): string => {
            return job?.annotators.find(({ id }) => id === annotatorId)?.username || '';
        },
        [job]
    );

    useEffect(() => {
        const newPageSize = apiPageSize && apiPageSize.height > 0 ? apiPageSize : originalPageSize;
        setPageSize!(newPageSize);
    }, [apiPageSize, originalPageSize]);

    const handleChangeScale = useCallback(() => {
        if (!containerRef.current || !apiPageSize || !apiPageSize.width) return;

        const { width } = containerRef.current.getBoundingClientRect();
        const newScale = getScale(width, apiPageSize.width);

        setScale(newScale);
    }, [apiPageSize]);

    const containerResizeObserver = useMemo(
        () => new ResizeObserver(handleChangeScale),
        [handleChangeScale]
    );

    useEffect(() => {
        if (!containerRef.current) return;
        containerResizeObserver.observe(containerRef.current);

        return () => {
            if (!containerRef.current) return;
            containerResizeObserver.unobserve(containerRef.current);
        };
    }, [containerResizeObserver]);

    const handlePageLoaded: PageLoadedCallback = (page) => {
        if (!originalPageSize) {
            if ('originalWidth' in page) {
                setOriginalPageSize({ width: page.originalWidth, height: page.originalHeight });
            } else {
                setOriginalPageSize({ width: page.naturalWidth, height: page.naturalHeight });
            }
        }
    };

    const handleDocumentLoaded = useCallback<DocumentLoadedCallback>(async (pdf) => {
        const page = await pdf.getPage(1);
        const { width, height } = page.getViewport({ scale: 1 });

        setOriginalPageSize({ width, height });
    }, []);

    const fullScale = scale + additionalScale;
    const annotatorIds = [
        ...new Set(latestRevisionByAnnotators.map((revision) => revision.user_id))
    ];

    return (
        <div
            className={cx(
                styles['pdf-container'],
                job?.validation_type === ValidationType.extensiveCoverage &&
                    styles['with-multiple-view']
            )}
        >
            <div ref={containerRef} className={styles['pdf-document-container']}>
                {isSplitValidation ? (
                    <Document
                        file={getPdfDocumentAddress(fileMetaInfo.id)}
                        loading={<Spinner color="sky" />}
                        options={{ httpHeaders: getAuthHeaders() }}
                        className={cn(styles['split-document-wrapper'], {
                            [styles[`vertical-view--pages-${annotatorIds.length + 1}`]]:
                                gridVariant === GridVariants.vertical,
                            [styles[`horizontal-view--pages-${annotatorIds.length + 1}`]]:
                                gridVariant === GridVariants.horizontal
                        })}
                    >
                        <ResizableSyncedContainer
                            type={gridVariant}
                            rowsCount={latestRevisionByAnnotators.length + 1}
                            className={styles['split-document-page']}
                        >
                            {pageNumbers.map((pageNum, orderNumber) => {
                                return (
                                    <Fragment key={`validation-${pageNum}`}>
                                        <DocumentSinglePage
                                            scale={fullScale}
                                            pageSize={apiPageSize}
                                            pageNum={pageNum}
                                            orderNumber={orderNumber}
                                            handlePageLoaded={handlePageLoaded}
                                            containerRef={containerRef}
                                            editable
                                            isShownAnnotation={true}
                                            onAnnotationCopyPress={onAnnotationCopyPress}
                                            onAnnotationCutPress={onAnnotationCutPress}
                                            onAnnotationPastePress={onAnnotationPastePress}
                                            onAnnotationUndoPress={onAnnotationUndoPress}
                                            onAnnotationRedoPress={onAnnotationRedoPress}
                                            onEmptyAreaClick={onEmptyAreaClick}
                                            isScrolledToCurrent={
                                                pageNum === currentOrderPageNumber + 1
                                            }
                                        />
                                    </Fragment>
                                );
                            })}
                        </ResizableSyncedContainer>

                        {annotatorIds.map((userId) => (
                            <div key={userId} className={styles['additional-pages-with-user-name']}>
                                <SplitAnnotatorInfo annotatorName={getAnnotatorName(userId)} />
                                <SyncedContainer
                                    className={cx(
                                        styles['split-document-page'],
                                        styles['additional-page']
                                    )}
                                >
                                    {pageNumbers.map((pageNum, orderNumber) => {
                                        const isShowAnnotation =
                                            !!latestRevisionByAnnotatorsWithBounds[userId].filter(
                                                (obj) => obj.pageNum === pageNum
                                            ).length;

                                        return (
                                            <DocumentSinglePage
                                                key={`${userId}-${pageNum}`}
                                                scale={fullScale}
                                                pageNum={pageNum}
                                                orderNumber={orderNumber}
                                                pageSize={apiPageSize}
                                                userId={userId}
                                                isShownAnnotation={isShowAnnotation}
                                                annotations={
                                                    latestRevisionByAnnotatorsWithBounds[userId]
                                                }
                                                onAnnotationSelected={(scaledAnn?: Annotation) =>
                                                    onSplitAnnotationSelected(
                                                        fullScale,
                                                        userId,
                                                        scaledAnn
                                                    )
                                                }
                                                isScrolledToCurrent={
                                                    pageNum === currentOrderPageNumber + 1
                                                }
                                            />
                                        );
                                    })}
                                </SyncedContainer>
                            </div>
                        ))}
                    </Document>
                ) : selectedRelatedDoc ? (
                    <div
                        className={cn(
                            styles['split-document-wrapper'],
                            styles[`split-document-wrapper--pages-2`]
                        )}
                    >
                        <SyncedContainer className={styles['split-document-page']}>
                            <Document
                                file={getPdfDocumentAddress(fileMetaInfo.id)}
                                loading={<Spinner color="sky" />}
                                options={{ httpHeaders: getAuthHeaders() }}
                            >
                                <DocumentSinglePage
                                    scale={fullScale}
                                    pageSize={apiPageSize}
                                    pageNum={currentPage}
                                    orderNumber={currentOrderPageNumber}
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
                            </Document>
                        </SyncedContainer>
                        <SyncedContainer className={styles['split-document-page']}>
                            <Document
                                file={getPdfDocumentAddress(selectedRelatedDoc.id)}
                                loading={<Spinner color="sky" />}
                                options={{ httpHeaders: getAuthHeaders() }}
                            >
                                <DocumentSinglePage
                                    annotations={[]}
                                    scale={fullScale}
                                    pageSize={apiPageSize}
                                    pageNum={currentPage}
                                    orderNumber={currentOrderPageNumber}
                                    handlePageLoaded={handlePageLoaded}
                                    containerRef={containerRef}
                                    editable={false}
                                    onAnnotationCopyPress={onAnnotationCopyPress}
                                    onAnnotationCutPress={onAnnotationCutPress}
                                    onAnnotationPastePress={onAnnotationPastePress}
                                    onAnnotationUndoPress={onAnnotationUndoPress}
                                    onAnnotationRedoPress={onAnnotationRedoPress}
                                    onEmptyAreaClick={onEmptyAreaClick}
                                />
                            </Document>
                        </SyncedContainer>
                    </div>
                ) : (
                    <>
                        {fileMetaInfo.extension === '.pdf' ? (
                            <DocumentPDF
                                ref={documentPDFRef}
                                fileMetaInfo={fileMetaInfo}
                                pageNumbers={pageNumbers}
                                fullScale={fullScale}
                                pageSize={apiPageSize}
                                handleDocumentLoaded={handleDocumentLoaded}
                                containerRef={containerRef}
                                editable={editable}
                            />
                        ) : null}
                        {fileMetaInfo.extension === '.jpg' ? (
                            <div className={styles['images-container']}>
                                {pageNumbers.map((pageNum, orderNumber) => {
                                    return (
                                        <Fragment key={pageNum}>
                                            <DocumentSinglePage
                                                scale={fullScale}
                                                pageSize={apiPageSize}
                                                pageNum={pageNum}
                                                orderNumber={orderNumber}
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
                                                isScrolledToCurrent={
                                                    pageNum === currentOrderPageNumber + 1
                                                }
                                            />
                                        </Fragment>
                                    );
                                })}
                            </div>
                        ) : null}
                    </>
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
            renderTextLayer={false}
            width={pageSize?.width}
            height={pageSize?.height}
        />
    );
};

export default DocumentPages;
