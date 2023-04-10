import React, {
    Fragment,
    ReactNode,
    useEffect,
    useState,
    useRef,
    useCallback,
    useMemo
} from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
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

export interface PageSize {
    width: number;
    height: number;
}

type DocumentPagesProps = {
    renderLinks?: (params: RenderLinksParams) => ReactNode;
    pageNumbers?: number[];
    fileMetaInfo: FileMetaInfo;
    apiPageSize?: PageSize;
    additionalScale: number;
    setPageSize?: (nS: any) => void;

    editable: boolean;
    onAnnotationCopyPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationCutPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationPastePress: (pageSize: PageSize, pageNum: number) => void;
    onAnnotationUndoPress: () => void;
    onAnnotationRedoPress: () => void;
    onEmptyAreaClick: () => void;
};

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
    additionalScale,
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
        categoriesByUserId,
        currentPage,
        isSplitValidation,
        onSplitAnnotationSelected,
        userPages,
        selectedLabels,
        selectedRelatedDoc,
        job
    } = useTaskAnnotatorContext();

    const containerRef = useRef<HTMLDivElement>(null);

    const [scale, setScale] = useState(0);
    const [originalPageSize, setOriginalPageSize] = useState<PageSize>();

    const selectedLabelsId = useMemo(
        () => selectedLabels?.map(({ id }) => id) || [],
        [selectedLabels]
    );

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

    const handlePageLoaded = (page: PDFPageProxy | HTMLImageElement) => {
        if (!originalPageSize) {
            if ('originalWidth' in page) {
                setOriginalPageSize({ width: page.originalWidth, height: page.originalHeight });
            } else {
                setOriginalPageSize({ width: page.naturalWidth, height: page.naturalHeight });
            }
        }
    };

    const fullScale = scale + additionalScale;

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
                        className={cn(
                            styles['split-document-wrapper'],
                            styles[`split-document-wrapper--pages-${userPages.length + 1}`]
                        )}
                    >
                        <ResizableSyncedContainer className={styles['split-document-page']}>
                            <DocumentSinglePage
                                scale={fullScale}
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
                        </ResizableSyncedContainer>
                        {userPages.map(({ user_id, page_num }) => (
                            <Fragment key={user_id}>
                                <SplitAnnotatorInfo
                                    annotatorName={getAnnotatorName(user_id)}
                                    labels={categoriesByUserId[user_id]}
                                    selectedLabelsId={selectedLabelsId}
                                />
                                <SyncedContainer className={styles['split-document-page']}>
                                    <DocumentSinglePage
                                        userId={user_id}
                                        annotations={annotationsByUserId[user_id]}
                                        scale={fullScale}
                                        pageSize={apiPageSize}
                                        pageNum={page_num}
                                        onAnnotationSelected={(scaledAnn?: Annotation) =>
                                            onSplitAnnotationSelected(fullScale, user_id, scaledAnn)
                                        }
                                    />
                                </SyncedContainer>
                            </Fragment>
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
                                                    scale={fullScale}
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
                                                scale={fullScale}
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
