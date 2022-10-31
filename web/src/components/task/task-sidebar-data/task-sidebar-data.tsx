import React, { FC } from 'react';
import { Text, TextArea } from '@epam/loveship';
import styles from './task-sidebar-data.module.scss';
import { CategoryDataAttributeWithValue } from 'api/typings';

type TaskSidebarDataProps = {
    isCategoryDataEmpty: boolean;
    annDataAttrs?: Record<number, CategoryDataAttributeWithValue[]>;
    selectedAnnotationId?: number;
    onDataAttributesChange: (elIndex: number, value: string) => void;
    viewMode: boolean;
};

export const TaskSidebarData: FC<TaskSidebarDataProps> = ({
    annDataAttrs,
    selectedAnnotationId,
    isCategoryDataEmpty,
    onDataAttributesChange,
    viewMode
}) => {
    return (
        <div className={styles['task-sidebar-data']}>
            {isCategoryDataEmpty && (
                <Text>{`The selected category doesn't have data attributes`}</Text>
            )}
            {annDataAttrs &&
                selectedAnnotationId &&
                annDataAttrs[+selectedAnnotationId] &&
                annDataAttrs[+selectedAnnotationId].map(({ name, type, value }, index) => {
                    return (
                        <div key={`${name}${type}`}>
                            <Text>{name}</Text>
                            <TextArea
                                rows={6}
                                value={value}
                                onValueChange={(val) => {
                                    onDataAttributesChange(index, val);
                                }}
                                isDisabled={viewMode}
                            />
                        </div>
                    );
                })}
        </div>
    );
};
