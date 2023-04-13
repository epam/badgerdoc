import React, { FC } from 'react';
import { Annotation } from 'shared';
import { stringToRGBA } from 'shared/components/annotator/utils/string-to-rgba';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Text } from '@epam/loveship';
import { cx } from '@epam/uui';

import styles from './styles.module.scss';
import { Link } from 'api/typings';
import { Links } from './links';

export const AnnotationRow: FC<
    Annotation & {
        index: number;
        incomingLinks?: Annotation['links'];
        annotationNameById: Record<string, string>;
        onSelect: (index: number) => void;
        onSelectById: (id: Annotation['id']) => void;
        selectedAnnotationId?: Annotation['id'];
        isEditable: boolean;
        onLinkDeleted: (pageNum: number, annotationId: Annotation['id'], link: Link) => void;
    }
> = ({
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
            <div
                className={styles.label}
                style={{
                    color,
                    backgroundColor: stringToRGBA(color, 0.2)
                }}
            >
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
