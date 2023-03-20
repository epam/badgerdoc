import React, { FC } from 'react';
import { PDFPageProxy } from 'react-pdf/dist/Page';
import { Annotation, Annotator, AnnotationLabel } from 'shared';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import ContextMenu, { useContextMenu } from '../context-menu/context-menu';
import ObservedElement from '../observed-element/observed-element';
import styles from '../../../components/task/task-document-pages/task-document-pages.module.scss';
import { useTableAnnotatorContext } from '../annotator/context/table-annotator-context';
import { defaultRenderPage } from './document-pages';
import { Category } from '../../../api/typings';
import { noop } from 'lodash';

const empty: any[] = [];

const DocumentSinglePage: FC<RenderPageParams> = ({
    annotations,
    scale,
    pageNum,
    userId,
    handlePageLoaded = noop,
    pageSize,
    containerRef,
    editable = false,
    isImage = false,
    imageId,
    onAnnotationCopyPress = noop,
    onAnnotationCutPress = noop,
    onAnnotationSelected,
    onAnnotationPastePress = noop,
    onAnnotationUndoPress = noop,
    onAnnotationRedoPress = noop,
    onEmptyAreaClick = noop
}) => {
    const {
        task,
        selectedCategory,
        allAnnotations = {},
        tokensByPages,
        categories,
        selectionType,
        currentPage,
        editedPages,
        validPages,
        invalidPages,
        onAnnotationCreated,
        onAnnotationDeleted,
        onAnnotationEdited,
        onCurrentPageChange,
        onAnnotationDoubleClick,
        isSplitValidation,
        setCurrentDocumentUserId
    } = useTaskAnnotatorContext();
    const { showMenu, getMenuProps } = useContextMenu();
    const pageAnnotations = annotations ?? allAnnotations[pageNum] ?? empty;

    const isValidation = task?.is_validation;
    const isEdited = editedPages.includes(currentPage);
    const pageTokens = tokensByPages[pageNum] ?? empty;
    const { isCellMode } = useTableAnnotatorContext();
    const handleAnnotationAdded = (ann: Pick<Annotation, 'bound' | 'boundType' | 'id'>) => {
        onAnnotationCreated(pageNum, {
            ...ann,
            category: selectedCategory?.id
        });
    };
    const handleAnnotationDeleted = (annotationId: string | number) => {
        onAnnotationDeleted(pageNum, annotationId);
    };
    const handleAnnotationEdited = (
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => {
        onAnnotationEdited(pageNum, annotationId, changes);
    };
    const handleAnnotationContextMenu = (
        event: React.MouseEvent,
        annotationId: string | number,
        labels?: AnnotationLabel[]
    ) => {
        showMenu(event, { annotationId, pageNum, pageSize, labels });
    };
    const categoryColor = selectedCategory?.metadata?.color;
    const annotationStyle: Pick<React.CSSProperties, 'border'> = {
        border: `2px ${categoryColor} solid`
    };
    const isValid = validPages.includes(currentPage);
    const isInvalid = invalidPages.includes(currentPage);
    const validationStyle = `${styles.validation} ${
        isValid ? styles.validColor : styles.invalidColor
    }`;
    const isValidationProcessed = isValid || isInvalid;

    type MenuItem = {
        id: ('cut' | 'copy' | 'paste' | 'undo' | 'redo') | number;
        name: string;
        category?: Category;
        shortcut?: string;
    };

    const mappedCategories = categories
        ? categories.map(
              (category) =>
                  ({
                      id: category.id,
                      name: category.name,
                      category
                  } as MenuItem)
          )
        : [];

    const menuItems: MenuItem[] = [
        ...mappedCategories,
        { id: 'cut', name: 'Cut', shortcut: 'Ctrl+X' },
        { id: 'copy', name: 'Copy', shortcut: 'Ctrl+C' },
        { id: 'paste', name: 'Paste', shortcut: 'Ctrl+V' },
        { id: 'undo', name: 'Undo', shortcut: 'Ctrl+Z' },
        { id: 'redo', name: 'Redo', shortcut: 'Ctrl+Y' }
    ];
    return (
        <ObservedElement
            rootRef={containerRef}
            onIntersect={() => {
                onCurrentPageChange(pageNum);
            }}
            disabled={!pageSize}
            width={pageSize ? pageSize.width * scale : undefined}
            height={pageSize ? pageSize.height * scale : undefined}
            className={styles.page}
        >
            <div
                role="none"
                onClick={() => {
                    setCurrentDocumentUserId(userId);
                }}
                style={{
                    opacity: isValidation && pageNum !== currentPage ? 0.4 : 1
                }}
            >
                {pageNum === currentPage && isValidationProcessed && !isSplitValidation ? (
                    <div className={validationStyle} />
                ) : null}
                <Annotator
                    key={pageNum}
                    scale={scale}
                    annotations={pageAnnotations}
                    tokens={pageTokens}
                    tokenStyle={{
                        background: categoryColor,
                        opacity: 0.2
                    }}
                    onAnnotationAdded={handleAnnotationAdded}
                    onAnnotationContextMenu={handleAnnotationContextMenu}
                    onAnnotationDeleted={
                        isEdited || !isValidation || isSplitValidation
                            ? handleAnnotationDeleted
                            : undefined
                    }
                    onAnnotationEdited={handleAnnotationEdited}
                    onAnnotationDoubleClick={onAnnotationDoubleClick}
                    onAnnotationCopyPress={(annotationId) =>
                        onAnnotationCopyPress(pageNum, annotationId)
                    }
                    onAnnotationCutPress={(annotationId) =>
                        onAnnotationCutPress(pageNum, annotationId)
                    }
                    onAnnotationSelected={onAnnotationSelected}
                    onAnnotationPastePress={() =>
                        pageSize && onAnnotationPastePress(pageSize, pageNum)
                    }
                    onAnnotationUndoPress={onAnnotationUndoPress}
                    onAnnotationRedoPress={onAnnotationRedoPress}
                    onEmptyAreaClick={onEmptyAreaClick}
                    annotationStyle={{
                        'free-box': annotationStyle,
                        box: annotationStyle,
                        table: annotationStyle,
                        text: annotationStyle,
                        table_cell: annotationStyle,
                        polygon: annotationStyle
                    }}
                    selectionStyle={annotationStyle}
                    selectionType={selectionType}
                    selectedCategory={selectedCategory}
                    categories={categories}
                    isCellMode={isCellMode}
                    page={pageNum}
                    editable={editable}
                >
                    {defaultRenderPage({
                        scale,
                        pageNum,
                        handlePageLoaded,
                        pageSize,
                        isImage,
                        imageId
                    })}
                </Annotator>
            </div>
            <ContextMenu
                menuItems={menuItems}
                renderMenuItem={(menuItem) => {
                    if (menuItem.category) {
                        return (
                            <div style={{ color: menuItem.category.metadata?.color }}>
                                {menuItem.category.name}
                            </div>
                        );
                    } else {
                        return <div>{menuItem.name}</div>;
                    }
                }}
                onMenuItemClick={(menuItem, data) => {
                    const labelToChangeIdx: number = data.labels.findIndex(
                        (label: AnnotationLabel) => label.annotationId === data.annotationId
                    );

                    const changedLabel: AnnotationLabel = {
                        ...data.labels[labelToChangeIdx],
                        color: menuItem?.category?.metadata?.color,
                        label: menuItem?.category?.name
                    };
                    data.labels[labelToChangeIdx] = changedLabel;
                    if (menuItem.category) {
                        onAnnotationEdited(data.pageNum, data.annotationId, {
                            category: menuItem.category.id,
                            color: menuItem.category.metadata?.color,
                            label: menuItem.category.name,
                            labels: data.labels
                        });
                    } else {
                        switch (menuItem.id) {
                            case 'cut':
                                onAnnotationCutPress(data.pageNum, data.annotationId);
                                break;

                            case 'copy':
                                onAnnotationCopyPress(data.pageNum, data.annotationId);
                                break;

                            case 'paste':
                                onAnnotationPastePress(data.pageSize, data.pageNum);
                                break;

                            case 'undo':
                                onAnnotationUndoPress();
                                break;

                            case 'redo':
                                onAnnotationRedoPress();
                                break;
                        }
                    }
                }}
                {...getMenuProps()}
            />
        </ObservedElement>
    );
};

type RenderPageParams = {
    userId?: string;
    annotations?: Annotation[];
    scale: number;
    pageNum: number;
    handlePageLoaded?: (page: PDFPageProxy | HTMLImageElement) => void;
    pageSize?: PageSize;
    containerRef?: React.RefObject<HTMLDivElement>;
    editable?: boolean;
    isImage?: boolean;
    imageId?: number;
    onAnnotationCopyPress?: (pageNum: number, annotationId: string | number) => void;
    onAnnotationCutPress?: (pageNum: number, annotationId: string | number) => void;
    onAnnotationPastePress?: (pageSize: PageSize, pageNum: number) => void;
    onAnnotationSelected?: (annotation?: Annotation) => void;
    onAnnotationUndoPress?: () => void;
    onAnnotationRedoPress?: () => void;
    onEmptyAreaClick?: () => void;
};

interface PageSize {
    width: number;
    height: number;
}

export default DocumentSinglePage;
