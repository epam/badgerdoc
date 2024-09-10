// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import { FC, useCallback, useEffect, useRef, useState } from 'react';

import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { getAnnotationLabelColors, isContrastColor } from 'shared/helpers/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Links } from './links';
import { TAnnotationProps } from './types';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { Annotation } from 'shared';
import { useOutsideClick } from 'shared/helpers/utils';

import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { IconButton, Text, TextArea } from '@epam/loveship';
import { cx } from '@epam/uui';
import { ReactComponent as ContentEditFillIcon } from '@epam/assets/icons/common/content-edit-24.svg';

import styles from './task-sidebar-flow.module.scss';

export const AnnotationRow: FC<TAnnotationProps> = ({
    id,
    color = '',
    label = '',
    text,
    index,
    pageNum,
    onSelect,
    onSelectById,
    categoryName,
    selectedAnnotationId,
    annotationNameById,
    incomingLinks,
    links,
    isEditable,
    isClosable,
    onLinkDeleted,
    onCloseIconClick
}) => {
    const [isEditMode, setIsEditMode] = useState<boolean>(false);
    const [annotationText, setAnnotationText] = useState<string>('');
    const [annotation, setAnnotation] = useState<Annotation>();

    const { allAnnotations, currentPage, onAnnotationEdited, revisionId } =
        useTaskAnnotatorContext();

    const labelList = label.split('.');
    const onIconClick = useCallback(
        (event) => {
            onCloseIconClick(pageNum!, id);
            event.stopPropagation();
        },
        [pageNum, id, onCloseIconClick]
    );
    const ref = useRef(null);

    useOutsideClick(ref, () => {
        setIsEditMode(false);
    });

    useEffect(() => {
        if (annotation) {
            setAnnotationText(annotation.text ? annotation.text : '');
        }
    }, [annotation]);

    useEffect(() => {
        if (allAnnotations) {
            const ann = allAnnotations[currentPage]?.find((ann: Annotation) => {
                return ann.id === id;
            });
            setAnnotation(ann);
        }
    }, [allAnnotations, currentPage, id]);

    const handleAnnotationTextChange = (value: string) => {
        setAnnotationText(value);
        if (annotation) {
            onAnnotationEdited(currentPage, annotation.id, {
                text: value
            });
        }
    };

    return (
        <div
            role="none"
            onClick={() => onSelect(index)}
            id={`${ANNOTATION_FLOW_ITEM_ID_PREFIX}${id}`}
            className={cx(styles.item, id === selectedAnnotationId && styles.selectedAnnotation)}
        >
            <div className={styles.label} style={getAnnotationLabelColors(color)}>
                <Text cx={styles.labelText} rawProps={{ 'data-testid': 'flow-label' }}>
                    {labelList[labelList.length - 1]}
                </Text>
                {isClosable && !revisionId && (
                    <IconButton
                        icon={closeIcon}
                        cx={styles.close}
                        iconPosition={'right'}
                        onClick={onIconClick}
                        color={isContrastColor(color) ? 'white' : 'night900'}
                    />
                )}
                {!links?.length && !incomingLinks?.length ? null : (
                    <Links
                        isEditable={isEditable}
                        onSelect={onSelectById}
                        links={links}
                        annotationId={id}
                        annotationPageNum={pageNum}
                        incomingLinks={incomingLinks}
                        onLinkDeleted={onLinkDeleted}
                        annotationNameById={annotationNameById}
                    />
                )}
            </div>
            {categoryName !== label && (
                <Text
                    color="night700"
                    cx={styles.pathContainer}
                    rawProps={{ 'data-testid': 'flow-path' }}
                >
                    {`${categoryName} ${ANNOTATION_PATH_SEPARATOR} `}
                    {labelList.join(` ${ANNOTATION_PATH_SEPARATOR} `)}
                </Text>
            )}
            <div className="flex-row flex-start justify-between" ref={ref}>
                {!isEditMode && (
                    <Text
                        cx={styles.text}
                        color="night500"
                        rawProps={{
                            style: {
                                marginRight: '8px'
                            }
                        }}
                    >
                        {text}
                    </Text>
                )}
                {isEditMode && (
                    <form onSubmit={() => setIsEditMode(false)} className={styles.textAreaForm}>
                        <TextArea
                            value={annotationText}
                            autoSize
                            cx="c-m-t-5"
                            onValueChange={handleAnnotationTextChange}
                            onBlur={() => setIsEditMode(false)}
                            rawProps={{
                                style: {
                                    marginRight: '8px'
                                }
                            }}
                        />
                    </form>
                )}
                {annotation?.boundType !== 'table' && !revisionId && (
                    <div
                        role="button"
                        onClick={() => setIsEditMode(true)}
                        onKeyPress={() => setIsEditMode(true)}
                        tabIndex={0}
                    >
                        <ContentEditFillIcon className={styles.editIcon} />
                    </div>
                )}
            </div>
        </div>
    );
};
