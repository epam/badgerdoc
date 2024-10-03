// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import { FC, useCallback, useEffect, useState } from 'react';
import { svc } from 'services';

import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { getAnnotationLabelColors, isContrastColor } from 'shared/helpers/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Links } from './links';
import { TAnnotationProps } from './types';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { Annotation } from 'shared';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { Checkbox, IconButton, LabeledInput, Text } from '@epam/loveship';
import { cx } from '@epam/uui';
import { ReactComponent as ContentEditFillIcon } from '@epam/assets/icons/common/content-edit-24.svg';
import { EditAnnotation, EditAnnotationModal } from './edit-annotation-modal';

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
    const [annotationValues, setAnnotationValues] = useState<EditAnnotation>({});
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

    useEffect(() => {
        if (annotation) {
            setAnnotationValues({
                text: annotation.text ? annotation.text : '',
                comment: annotation.comment ? annotation.comment : '',
                few_shot_learning: annotation.few_shot_learning
                    ? annotation.few_shot_learning
                    : false
            });
        }
    }, [annotation]);

    useEffect(() => {
        if (allAnnotations) {
            const allAnnsWithoutPage: Annotation[] = [];
            for (const pageNum in allAnnotations) {
                allAnnotations[pageNum].forEach((ann) => {
                    allAnnsWithoutPage.push(ann);
                });
            }
            const ann = allAnnsWithoutPage.find((ann: Annotation) => {
                return ann.id === id;
            });
            setAnnotation(ann);
        }
    }, [allAnnotations, currentPage, id]);

    const handleAnnotationChange = (formValues: EditAnnotation) => {
        if (annotation) {
            const page = annotation.pageNum ? annotation.pageNum : currentPage;
            onAnnotationEdited(page, annotation.id, {
                text: formValues.text,
                comment: formValues.comment,
                few_shot_learning: formValues.few_shot_learning
            });
        }
    };

    const showModal = () => {
        return svc.uuiModals
            .show((modalProps) => (
                <EditAnnotationModal
                    {...modalProps}
                    handleAnnotationChange={handleAnnotationChange}
                    annotationValues={annotationValues}
                />
            ))
            .catch(() => {});
    };

    return (
        <div
            role="none"
            onClick={() => onSelect(index)}
            id={`${ANNOTATION_FLOW_ITEM_ID_PREFIX}${id}`}
            className={cx(styles.item, id === selectedAnnotationId && styles.selectedAnnotation)}
        >
            <div className={styles.label} style={getAnnotationLabelColors(color)}>
                <div className={styles.linksText}>
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
                    <Text cx={styles.labelText} rawProps={{ 'data-testid': 'flow-label' }}>
                        {labelList[labelList.length - 1]}
                    </Text>
                </div>
                {isClosable && !revisionId && (
                    <IconButton
                        icon={closeIcon}
                        cx={styles.close}
                        iconPosition={'right'}
                        onClick={onIconClick}
                        color={isContrastColor(color) ? 'white' : 'night900'}
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
            <div className="flex-row flex-start justify-between">
                <div className={styles.annData}>
                    <Text cx={styles.text} color="night500">
                        {text}
                    </Text>
                    {annotationValues.comment && (
                        <LabeledInput label="Comment" cx={styles.commentLabel}>
                            <Text cx={styles.comment} color="night500">
                                {annotationValues.comment}
                            </Text>
                        </LabeledInput>
                    )}
                    {annotationValues.few_shot_learning && (
                        <Checkbox
                            label="Few-Shot Learning"
                            cx={styles.fewShotLearning}
                            value={annotationValues.few_shot_learning}
                            isReadonly
                            onValueChange={() => {}}
                        />
                    )}
                </div>
                {annotation?.boundType !== 'table' && !revisionId && (
                    <div
                        role="button"
                        onClick={showModal}
                        onKeyPress={showModal}
                        tabIndex={0}
                        className={styles.editIconContainer}
                    >
                        <ContentEditFillIcon className={styles.editIcon} />
                    </div>
                )}
            </div>
        </div>
    );
};
