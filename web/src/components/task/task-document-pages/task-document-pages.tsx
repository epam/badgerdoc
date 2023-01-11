import React from 'react';
import styles from './task-document-pages.module.scss';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import DocumentPages from 'shared/components/document-pages/document-pages';
import ExternalViewerPopup from 'components/external-viewer-modal/external-viewer-popup';

export interface DocumentPageProps {
    viewMode: boolean;
}

const TaskDocumentPages = (props: DocumentPageProps) => {
    const { viewMode } = props;
    const {
        task,
        fileMetaInfo,
        pageSize,
        setPageSize,
        pageNumbers,
        currentPage,
        editedPages,
        externalViewer,
        onEmptyAreaClick,
        onAnnotationCopyPress,
        onAnnotationCutPress,
        onAnnotationPastePress,
        onAnnotationUndoPress,
        onAnnotationRedoPress,
        onExternalViewerClose
    } = useTaskAnnotatorContext();

    const isValidation = task?.is_validation;
    const isEdited = editedPages.includes(currentPage);
    const editable = !viewMode && (!isValidation || isEdited);

    return (
        <div className={styles.container}>
            {externalViewer.isOpen && (
                <ExternalViewerPopup
                    onClose={onExternalViewerClose}
                    valueAttr={externalViewer.value}
                    nameAttr={externalViewer.name}
                    typeAttr={externalViewer.type}
                />
            )}
            <DocumentPages
                pageNumbers={pageNumbers}
                fileMetaInfo={fileMetaInfo}
                apiPageSize={pageSize}
                setPageSize={setPageSize}
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

export default TaskDocumentPages;
