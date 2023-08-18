import React, { Fragment } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { Document } from 'react-pdf';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';
import DocumentSinglePage from '../../document-single-page';
import { Spinner } from '@epam/loveship';
import styles from '../../document-pages.module.scss';
import { PageSize } from '../../document-pages';
import { PageLoadedCallback } from '../../types';

type DocumentPDFProps = {
    pageNumbers: number[];
    handlePageLoaded: PageLoadedCallback;
    fileMetaInfo: FileMetaInfo;
    apiPageSize?: PageSize;
    goToPage?: number;
    editable: boolean;
    fullScale: number;
    containerRef: {
        current: HTMLDivElement | null;
    };
};

const DocumentPDF: React.FC<DocumentPDFProps> = ({
    fileMetaInfo,
    pageNumbers,
    fullScale,
    apiPageSize,
    handlePageLoaded,
    containerRef,
    editable,
    goToPage
}) => {
    const {
        onEmptyAreaClick,
        onAnnotationCopyPress,
        onAnnotationCutPress,
        onAnnotationPastePress,
        onAnnotationUndoPress,
        onAnnotationRedoPress
    } = useTaskAnnotatorContext();

    return (
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
                                isScrolledToCurrent={pageNum === goToPage}
                            />
                        </Fragment>
                    );
                })}
            </Document>
        </>
    );
};

export default DocumentPDF;
