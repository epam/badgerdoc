import React, { CSSProperties, FC, useEffect, useMemo, useRef } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { Document } from 'react-pdf';
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import DocumentSinglePage from '../../document-single-page';
import { Spinner } from '@epam/loveship';
import { ANNOTATION_LABEL_ID_PREFIX } from 'shared/constants/annotations';
import { PageSize, DocumentLoadedCallback } from '../../types';
import { Annotation } from 'shared/components/annotator';

type DocumentPDFProps = {
    pageNumbers: number[];
    handleDocumentLoaded: DocumentLoadedCallback;
    fileMetaInfo: FileMetaInfo;
    pageSize?: PageSize;
    goToPage?: number;
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
    index,
    style
}) => {
    const pageNum = pageNumbers[index];
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

const isPointInsideRect = (point: { x: number; y: number }, rect: DOMRect): boolean => {
    return (
        point.x >= rect.left &&
        point.x <= rect.right &&
        point.y >= rect.top &&
        point.y <= rect.bottom
    );
};

const isRectIsFullyInAnotherRect = (rectIn: DOMRect, rectOut: DOMRect): boolean => {
    return (
        isPointInsideRect({ x: rectIn.left, y: rectIn.top }, rectOut) &&
        isPointInsideRect({ x: rectIn.right, y: rectIn.top }, rectOut) &&
        isPointInsideRect({ x: rectIn.right, y: rectIn.bottom }, rectOut) &&
        isPointInsideRect({ x: rectIn.left, y: rectIn.bottom }, rectOut)
    );
};

const getAnnotationLabelElement = ({ id }: { id: Annotation['id'] }): HTMLDivElement | null =>
    document.querySelector(`#${ANNOTATION_LABEL_ID_PREFIX}${id}`);

const DocumentPDF: React.FC<DocumentPDFProps> = ({
    fileMetaInfo,
    pageNumbers,
    fullScale,
    pageSize,
    handleDocumentLoaded,
    containerRef,
    editable,
    goToPage
}) => {
    const { selectedAnnotation } = useTaskAnnotatorContext();
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
    const apiToUiPageNumbersMap = useMemo<Map<number, number>>(() => {
        const map = pageNumbers.map((apiPageNum, uiPageNum) => [apiPageNum, uiPageNum] as const);
        return new Map(map);
    }, [pageNumbers]);
    const pdfPagesListRef = useRef<FixedSizeList>(null);
    const listViewContainerRef = useRef<HTMLDivElement>(null);
    const itemSize = Number(pageSize ? pageSize.height : 0) * fullScale;

    /**
     * goToPage - the ordering number of page which is currently shown on UI (starts from 1),
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
        pdfPagesListRef.current?.scrollToItem(goToPage! - 1, 'start');
    }, [goToPage]);

    // in case of scrolling to some annotation
    useEffect(() => {
        if (!selectedAnnotation || !pdfPagesListRef.current || !listViewContainerRef.current) {
            return;
        }

        const label = getAnnotationLabelElement(selectedAnnotation);

        if (label) {
            const isLabelVisible = isRectIsFullyInAnotherRect(
                label.getBoundingClientRect(),
                listViewContainerRef.current.getBoundingClientRect()
            );

            if (!isLabelVisible) {
                label.scrollIntoView();
            }
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
    }, [selectedAnnotation]);

    return (
        <>
            <Document
                file={getPdfDocumentAddress(fileMetaInfo.id)}
                loading={
                    <div className="flex-cell">
                        <Spinner color="sky" />
                    </div>
                }
                onLoadSuccess={handleDocumentLoaded}
                options={{ httpHeaders: getAuthHeaders() }}
            >
                <AutoSizer>
                    {({ width, height }: PageSize) => (
                        <FixedSizeList
                            outerRef={listViewContainerRef}
                            ref={pdfPagesListRef}
                            width={width}
                            height={height}
                            itemCount={pageNumbers.length}
                            itemData={pdfListData}
                            overscanCount={5}
                            style={fixedSizeListStyle}
                            itemSize={itemSize}
                        >
                            {PDFPageRenderer}
                        </FixedSizeList>
                    )}
                </AutoSizer>
            </Document>
        </>
    );
};

export default DocumentPDF;
