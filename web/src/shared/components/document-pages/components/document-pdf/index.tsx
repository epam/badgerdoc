// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import React, { CSSProperties, FC, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { Document } from 'react-pdf';
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import InfiniteLoader from 'react-window-infinite-loader';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import DocumentSinglePage from '../../document-single-page';
import { Spinner } from '@epam/loveship';
import { ANNOTATION_LABEL_ID_PREFIX } from 'shared/constants/annotations';
import { PageSize, DocumentLoadedCallback } from '../../types';
import { Annotation } from 'shared/components/annotator';
import { useDebouncedCallback } from 'use-debounce';
import { scrollIntoViewIfNeeded } from 'shared/helpers/scroll-into-view-if-needed';

type DocumentPDFProps = {
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

type ListItemData = Pick<
    DocumentPDFProps,
    'pageNumbers' | 'fullScale' | 'pageSize' | 'containerRef' | 'editable'
>;

type PDFPageRendererProps = {
    data: ListItemData;
    index: number;
    style: CSSProperties;
};

// "willChange: transform" set by react-window is removed
// to not create a new stacking context which may affect
// context menu we show via "position: fixed"
const fixedSizeListStyle = { willChange: 'auto' };

const PDFPageRenderer: FC<PDFPageRendererProps> = ({
    data: { pageNumbers, fullScale, pageSize, containerRef, editable },
    index: orderNumber,
    style
}) => {
    const pageNum = pageNumbers[orderNumber];
    const {
        onEmptyAreaClick,
        onAnnotationCopyPress,
        onAnnotationCutPress,
        onAnnotationPastePress,
        onAnnotationUndoPress,
        onAnnotationRedoPress
    } = useTaskAnnotatorContext();

    return (
        <div style={style}>
            <DocumentSinglePage
                scale={fullScale}
                pageSize={pageSize}
                pageNum={pageNum}
                orderNumber={orderNumber}
                containerRef={containerRef}
                editable={editable}
                onAnnotationCopyPress={onAnnotationCopyPress}
                onAnnotationCutPress={onAnnotationCutPress}
                onAnnotationPastePress={onAnnotationPastePress}
                onAnnotationUndoPress={onAnnotationUndoPress}
                onAnnotationRedoPress={onAnnotationRedoPress}
                onEmptyAreaClick={onEmptyAreaClick}
            />
        </div>
    );
};

const getAnnotationLabelElement = ({ id }: { id: Annotation['id'] }): HTMLDivElement | null =>
    document.querySelector(`#${ANNOTATION_LABEL_ID_PREFIX}${id}`);

// we trigger request a bit earlier in order to quicker show some
// data for the next scrolled PDF pages
const LOADING_THRESHOLD_BUFFER = 2;
const OVERSCAN_RENDERED_PAGES_COUNT = 5;

const DocumentPDF: React.FC<DocumentPDFProps> = ({
    fileMetaInfo,
    pageNumbers,
    fullScale,
    pageSize,
    handleDocumentLoaded,
    containerRef,
    editable
}) => {
    const {
        selectedAnnotation,
        setAvailableRenderedPagesRange,
        getNextDocumentItems,
        isDocumentPageDataLoaded,
        currentOrderPageNumber
    } = useTaskAnnotatorContext();
    const pdfListData = useMemo<ListItemData>(
        () => ({
            pageNumbers,
            fullScale,
            pageSize,
            containerRef,
            editable
        }),
        [pageNumbers, fullScale, pageSize, containerRef, editable]
    );
    const apiToUiPageNumbersMap = useMemo(() => {
        const map = pageNumbers.map((apiPageNum, uiPageNum) => [apiPageNum, uiPageNum] as const);
        return new Map(map);
    }, [pageNumbers]);
    const pdfPagesListRef = useRef<FixedSizeList | null>(null);
    const listViewContainerRef = useRef<HTMLDivElement>(null);
    const itemSize = Number(pageSize ? pageSize.height : 0) * fullScale;
    const loadMoreItems = useDebouncedCallback(getNextDocumentItems, 500);

    /**
     * currentOrderPageNumber - the ordering number of page which is currently shown on UI,
     * correlate with "pageNumbers (indexes)"
     * pageNumbers (values) - number of page comes from BE (can be started from any number
     * and contains numbers only for processed pages)
     * pageNumbers (indexes) - index of pageNumbers is a mapping to page numbers which comes from BE
     *
     * Example: [0: 22, 1: 23, 2: 25, 3: 28] (index - number of rendered page (actually, index + 1),
     * value - number of the page from BE)
     */

    // in case of page switching
    useEffect(() => {
        pdfPagesListRef.current?.scrollToItem(currentOrderPageNumber, 'start');
    }, [currentOrderPageNumber]);

    // in case of scrolling to some annotation
    useEffect(() => {
        // give the browser chance to make additional painting (to wait for changes with
        // annotations like creation of new annotation)
        requestAnimationFrame(() => {
            if (!selectedAnnotation || !pdfPagesListRef.current || !listViewContainerRef.current) {
                return;
            }

            const label = getAnnotationLabelElement(selectedAnnotation);

            if (label) {
                scrollIntoViewIfNeeded(listViewContainerRef.current, label);
            } else {
                const pageNum = apiToUiPageNumbersMap.get(selectedAnnotation.pageNum!)!;
                pdfPagesListRef.current.scrollToItem(pageNum - 1);

                // scroll to the annotation (in X and Y dimension) in async mode since
                // need to wait until scrollToItem() method loads the page -> DOM will
                // be ready with needed annotation
                requestAnimationFrame(() => {
                    getAnnotationLabelElement(selectedAnnotation)?.scrollIntoView();
                });
            }
        });
    }, [apiToUiPageNumbersMap, selectedAnnotation]);

    const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);
    const onDocumentLoadSuccess = useCallback(
        (pdf) => {
            handleDocumentLoaded(pdf);
            setIsDocumentLoaded(true);
        },
        [handleDocumentLoaded]
    );

    const isDocumentReadyForRender = isDocumentLoaded && itemSize > 0;

    return (
        <>
            <Document
                file={getPdfDocumentAddress(fileMetaInfo.id)}
                loading={
                    <div className="flex-cell">
                        <Spinner color="sky" />
                    </div>
                }
                onLoadSuccess={onDocumentLoadSuccess}
                options={{ httpHeaders: getAuthHeaders() }}
            >
                {isDocumentReadyForRender && (
                    <AutoSizer>
                        {({ width, height }: PageSize) => {
                            const countOfVisiblePages = Math.ceil(height / itemSize);
                            const loadingThreshold = countOfVisiblePages + LOADING_THRESHOLD_BUFFER;

                            return (
                                <InfiniteLoader
                                    isItemLoaded={isDocumentPageDataLoaded}
                                    itemCount={pageNumbers.length}
                                    loadMoreItems={loadMoreItems}
                                    threshold={loadingThreshold}
                                    minimumBatchSize={
                                        countOfVisiblePages + OVERSCAN_RENDERED_PAGES_COUNT
                                    }
                                >
                                    {({ onItemsRendered, ref }) => (
                                        <FixedSizeList
                                            ref={(listRef) => {
                                                ref(listRef);
                                                pdfPagesListRef.current = listRef;
                                            }}
                                            outerRef={listViewContainerRef}
                                            onItemsRendered={(props) => {
                                                setAvailableRenderedPagesRange({
                                                    begin: props.overscanStartIndex,
                                                    end: props.overscanStopIndex
                                                });
                                                onItemsRendered(props);
                                            }}
                                            width={width}
                                            height={height}
                                            itemCount={pageNumbers.length}
                                            itemData={pdfListData}
                                            overscanCount={OVERSCAN_RENDERED_PAGES_COUNT}
                                            style={fixedSizeListStyle}
                                            itemSize={itemSize}
                                        >
                                            {PDFPageRenderer}
                                        </FixedSizeList>
                                    )}
                                </InfiniteLoader>
                            );
                        }}
                    </AutoSizer>
                )}
            </Document>
        </>
    );
};

export default DocumentPDF;
