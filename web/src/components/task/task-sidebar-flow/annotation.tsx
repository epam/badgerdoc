import React, { FC } from 'react';
import { Annotation } from 'shared';
import { stringToRGBA } from 'shared/components/annotator/utils/string-to-rgba';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { ANNOTATION_PATH_SEPARATOR } from './constants';
import { Text } from '@epam/loveship';
import styles from './styles.module.scss';

export const AnnotationRow: FC<
    Annotation & {
        index: number;
        onSelect: (index: number) => void;
        selectedAnnotationId?: Annotation['id'];
    }
> = ({ id, color = '', label = '', text, index, onSelect, categoryName, selectedAnnotationId }) => {
    const labelList = label.split('.');

    return (
        <div id={`${ANNOTATION_FLOW_ITEM_ID_PREFIX}${id}`} className={styles.item}>
            <div
                style={{
                    color,
                    border: `1px solid ${color}`,
                    backgroundColor:
                        id !== selectedAnnotationId ? 'unset' : stringToRGBA(color, 0.2)
                }}
            >
                <Text
                    cx={styles.label}
                    onClick={() => onSelect(index)}
                    rawProps={{ 'data-testid': 'flow-label' }}
                >
                    {labelList[labelList.length - 1]}
                </Text>
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
