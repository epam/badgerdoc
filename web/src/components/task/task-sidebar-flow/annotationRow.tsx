import React, { FC, useCallback } from 'react';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Links } from './links';
import { TAnnotationProps } from './types';
import { getAnnotationLabelColors, isContrastColor } from 'shared/helpers/annotations';

import { Text, IconButton } from '@epam/loveship';
import { cx } from '@epam/uui';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';

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
    onLinkDeleted,
    onCloseIconClick
}) => {
    const labelList = label.split('.');
    const onIconClick = useCallback(
        (event) => {
            onCloseIconClick(pageNum!, id);
            event.stopPropagation();
        },
        [pageNum, id, onCloseIconClick]
    );

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
                <IconButton
                    icon={closeIcon}
                    cx={styles.close}
                    iconPosition={'right'}
                    onClick={onIconClick}
                    color={isContrastColor(color) ? 'white' : 'night900'}
                />
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
            <Text cx={styles.text} color="night500">
                {text}
            </Text>
        </div>
    );
};
