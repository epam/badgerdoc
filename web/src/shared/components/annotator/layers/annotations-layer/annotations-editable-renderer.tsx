import React, { RefObject } from 'react';
import { BoxAnnotation } from '../../components/box-annotation';
import { EditableAnnotationRenderer, PageToken } from '../../typings';
import { TextAnnotation } from '../../components/text-annotation';
import { TableAnnotation } from '../../components/table-annotation';
import { ImageAnnotation } from '../../components/image-annotation';

export const editableAnnotationRenderer: EditableAnnotationRenderer = ({
    annotation,
    cells,
    isSelected,
    isHovered,
    scale,
    selectedAnnotationRef,
    onClick,
    onDoubleClick,
    editable,
    onContextMenu,
    onAnnotationContextMenu,
    onCloseIconClick,
    onAnnotationDelete,
    onMouseEnter,
    onMouseLeave,
    panoRef,
    isCellMode,
    page,
    categories,
    tools,
    setTools,
    canvas,
    taskHasTaxonomies
}) => {
    switch (annotation.boundType) {
        case 'box':
        case 'free-box':
            return (
                <BoxAnnotation
                    isEditable={editable}
                    isSelected={isSelected}
                    isHovered={isHovered}
                    key={annotation.id}
                    annotationRef={selectedAnnotationRef}
                    bound={annotation.bound}
                    color={annotation.color}
                    label={annotation.label}
                    onClick={onClick}
                    onDoubleClick={onDoubleClick}
                    onContextMenu={onContextMenu}
                    onCloseIconClick={onCloseIconClick}
                    id={annotation.id}
                    page={page!}
                    boundType={annotation.boundType}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                    taskHasTaxonomies={taskHasTaxonomies}
                />
            );
        case 'text':
            return (
                <TextAnnotation
                    isEditable={editable}
                    isSelected={isSelected}
                    isHovered={isHovered}
                    key={annotation.id}
                    tokens={annotation.tokens as PageToken[]}
                    color={annotation.color}
                    label={annotation.label}
                    labels={annotation.labels}
                    scale={scale as number}
                    onClick={onClick}
                    onDoubleClick={onDoubleClick}
                    onContextMenu={onContextMenu}
                    onAnnotationContextMenu={onAnnotationContextMenu}
                    onAnnotationDelete={onAnnotationDelete}
                    id={annotation.id}
                    page={page!}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                    taskHasTaxonomies={taskHasTaxonomies}
                />
            );
        case 'table':
            return (
                <TableAnnotation
                    isEditable={editable}
                    isSelected={isSelected}
                    key={annotation.id}
                    annotationRef={selectedAnnotationRef}
                    bound={annotation.bound}
                    color={annotation.color}
                    label={annotation.label}
                    onClick={onClick}
                    onContextMenu={onContextMenu}
                    onDoubleClick={onDoubleClick}
                    onCloseIconClick={onCloseIconClick}
                    panoRef={panoRef as RefObject<HTMLDivElement>}
                    annotation={annotation}
                    scale={scale as number}
                    isCellMode={isCellMode as boolean}
                    id={annotation.id}
                    page={page!}
                    cells={annotation.tableCells}
                    categories={categories}
                />
            );
        case 'polygon':
            return (
                <ImageAnnotation
                    annotation={annotation}
                    isEditable={editable}
                    isSelected={isSelected}
                    isHovered={isHovered}
                    key={annotation.id}
                    annotationRef={selectedAnnotationRef}
                    bound={annotation.bound}
                    color={annotation.color}
                    label={annotation.label}
                    onClick={onClick}
                    onDoubleClick={onDoubleClick}
                    onContextMenu={onContextMenu}
                    onCloseIconClick={onCloseIconClick}
                    id={annotation.id}
                    page={page!}
                    boundType={annotation.boundType}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                    segments={annotation.segments!}
                    tools={tools}
                    setTools={setTools}
                    canvas={canvas}
                    scale={scale as number}
                />
            );
        default:
            return <></>;
    }
};
