import React, { useRef, useState } from 'react';
import styles from './task-document-pages.module.scss';
import { Annotation } from 'shared';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import DocumentPages from 'shared/components/document-pages/document-pages';
import { useTableAnnotatorContext } from '../../../shared/components/annotator/context/table-annotator-context';
import ExternalViewerPopup from 'components/external-viewer-modal/external-viewer-popup';
import { getPointsForLinks } from 'shared/components/annotator/utils/get-points-for-link';
import { LinkAnnotation } from 'shared/components/annotator/components/link-annotation';
import { useAnnotationsLinks } from 'shared/components/annotator/utils/use-annotation-links';

const empty: any[] = [];

export interface DocumentPageProps {
    viewMode: boolean;
}

const TaskDocumentPages = (props: DocumentPageProps) => {
    const { viewMode } = props;
    const {
        task,
        selectedCategory,
        fileMetaInfo,
        allAnnotations = {},
        tokensByPages,
        categories,
        pageSize,
        setPageSize,
        selectionType,
        pageNumbers,
        currentPage,
        editedPages,
        validPages,
        invalidPages,
        externalViewer,
        selectedAnnotation,
        onAnnotationCreated,
        onAnnotationDeleted,
        onAnnotationEdited,
        onLinkDeleted,
        onCurrentPageChange,
        onEmptyAreaClick,
        onAnnotationDoubleClick,
        onAnnotationCopyPress,
        onAnnotationCutPress,
        onAnnotationPastePress,
        onAnnotationUndoPress,
        onAnnotationRedoPress,
        onExternalViewerClose
    } = useTaskAnnotatorContext();
    const { isCellMode } = useTableAnnotatorContext();

    const containerRef = useRef<HTMLDivElement>(null);

    const isValidation = task?.is_validation;
    const isEdited = editedPages.includes(currentPage);

    const annotatorLinks = useAnnotationsLinks(
        selectedAnnotation,
        selectedCategory,
        currentPage,
        selectionType,
        allAnnotations,
        (prevPage, links, annId) => selectedAnnotation && onAnnotationEdited(prevPage, annId, links)
    );

    const isValid = validPages.includes(currentPage);
    const isInvalid = invalidPages.includes(currentPage);
    const validationStyle = `${styles.validation} ${
        isValid ? styles.validColor : styles.invalidColor
    }`;
    const isValidationProcessed = isValid || isInvalid;
    const editable = !viewMode && (!isValidation || isEdited);

    return (
        <div ref={containerRef} className={styles.container}>
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
                annotatorLinks={annotatorLinks}
                editable={editable}
                containerRef={containerRef}
                onAnnotationCopyPress={onAnnotationCopyPress}
                onAnnotationCutPress={onAnnotationCutPress}
                onAnnotationPastePress={onAnnotationPastePress}
                onAnnotationUndoPress={onAnnotationUndoPress}
                onAnnotationRedoPress={onAnnotationRedoPress}
                onEmptyAreaClick={onEmptyAreaClick}
                renderLinks={(params) => {
                    const { scale, updLinks } = params;
                    const anns = ([] as Annotation[]).concat.apply(
                        [],
                        Object.values(allAnnotations)
                    );

                    return (Object.keys(allAnnotations) as unknown as number[]).map(
                        (key: number) => {
                            return allAnnotations[key].map((ann: Annotation) => {
                                return (
                                    ann.links?.length &&
                                    getPointsForLinks(
                                        ann.id,
                                        ann.boundType,
                                        key,
                                        ann.links,
                                        anns,
                                        categories
                                    ).map((pointSet) => {
                                        return (
                                            <LinkAnnotation
                                                key={ann.id}
                                                pointStart={pointSet.start}
                                                pointFinish={pointSet.finish}
                                                category={pointSet.category}
                                                linkType={pointSet.type}
                                                reversed={pointSet.finish.id === ann.id}
                                                onDeleteLink={() =>
                                                    onLinkDeleted(key, ann.id, pointSet.link)
                                                }
                                            />
                                        );
                                    })
                                );
                            });
                        }
                    );
                }}
            />
        </div>
    );
};

export default TaskDocumentPages;
