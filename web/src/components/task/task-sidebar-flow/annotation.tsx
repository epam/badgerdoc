import React, { FC } from 'react';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Text } from '@epam/loveship';
import { cx } from '@epam/uui';

import styles from './styles.module.scss';
import { Links } from './links';
import { TAnnotationProps } from './types';
import { getAnnotationLabelColors } from 'shared/helpers/annotations';

export const AnnotationRow: FC<TAnnotationProps> = ({
    id,
    color = '',
    label = '',
    text,
    index,
    onSelect,
    onSelectById,
    categoryName,
    selectedAnnotationId,
    annotationNameById,
    incomingLinks,
    links,
    isEditable,
    onLinkDeleted
}) => {
    const labelList = label.split('.');

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
                {!links?.length && !incomingLinks?.length ? null : (
                    <Links
                        isEditable={isEditable}
                        onSelect={onSelectById}
                        links={links}
                        annotationId={id}
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
