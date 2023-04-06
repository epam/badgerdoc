import React from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import DocumentPages from 'shared/components/document-pages/document-pages';
import ExternalViewerPopup from 'components/external-viewer-modal/external-viewer-popup';
import styles from './task-document-pages.module.scss';

export interface DocumentPageProps {
    viewMode: boolean;
}

const TaskDocumentPages = ({ viewMode }: DocumentPageProps) => {
    const {
        task,
        fileMetaInfo,
        pageSize,
        setPageSize,
        pageNumbers,
        currentPage,
        editedPages,
        externalViewer,
        onExternalViewerClose
    } = useTaskAnnotatorContext();

    const isValidation = task?.is_validation;
    const isReady = task?.status === 'Ready';
    const isInProgress = task?.status === 'In Progress';
    const isEdited = editedPages.includes(currentPage);
    const editable = !viewMode && (!isValidation || isEdited) && (isReady || isInProgress);

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
            />
        </div>
    );
};

export default TaskDocumentPages;
