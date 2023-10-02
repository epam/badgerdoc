// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { FC, Fragment, useRef, useState } from 'react';
import { CategoryDataAttributeWithValue } from 'api/typings';
import { TaxonomiesTree } from 'components/taxonomies/taxonomies-tree';
import { useTaxonomiesTree } from 'components/taxonomies/use-taxonomies-tree';
import { useHeight } from 'shared/hooks/use-height';
import { Annotation } from 'shared';
import { isEmpty } from 'lodash';
import { Blocker, SearchInput, Text, TextArea } from '@epam/loveship';
import styles from './task-sidebar-data.module.scss';
import { NoData } from 'shared/no-data';

type TaskSidebarDataProps = {
    isCategoryDataEmpty: boolean;
    annDataAttrs?: Record<number, CategoryDataAttributeWithValue[]>;
    selectedAnnotation?: Annotation;
    onDataAttributesChange: (elIndex: number, value: string) => void;
    viewMode: boolean;
    onAnnotationEdited: (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => void;
    currentPage: number;
    taxonomyId?: string;
};

export const TaskSidebarData: FC<TaskSidebarDataProps> = ({
    annDataAttrs,
    selectedAnnotation,
    isCategoryDataEmpty,
    onDataAttributesChange,
    viewMode,
    onAnnotationEdited,
    currentPage,
    taxonomyId
}) => {
    const [searchText, setSearchText] = useState('');

    const hightRef = useRef<HTMLDivElement>(null);
    const taxonomiesHeight = useHeight({ ref: hightRef });

    const { taxonomyNodes, expandNode, onLoadData, isLoading } = useTaxonomiesTree({
        searchText,
        taxonomyId
    });

    return (
        <div className={styles['task-sidebar-data']}>
            {isCategoryDataEmpty && (
                <div className={styles['no-data']}>
                    <NoData title="The selected category doesn't have data attributes" />
                </div>
            )}
            {annDataAttrs &&
                selectedAnnotation &&
                annDataAttrs[+selectedAnnotation.id] &&
                annDataAttrs[+selectedAnnotation.id].map(({ name, type, value }, index) => {
                    if (type === 'taxonomy') {
                        return (
                            <Fragment key={index}>
                                <SearchInput
                                    value={searchText}
                                    onValueChange={(text) => setSearchText(text ? text : '')}
                                    debounceDelay={300}
                                    cx={styles.search}
                                />
                                <div ref={hightRef} className={styles.tree}>
                                    <TaxonomiesTree
                                        isLoading={isLoading}
                                        key={searchText}
                                        taxonomiesHeight={taxonomiesHeight}
                                        taxonomyNodes={taxonomyNodes}
                                        onLoadData={onLoadData}
                                        expandNode={expandNode}
                                        selectedAnnotation={selectedAnnotation}
                                        onAnnotationEdited={onAnnotationEdited}
                                        currentPage={currentPage}
                                        onDataAttributesChange={onDataAttributesChange}
                                        elementIndex={index}
                                        selectedKey={value}
                                        defaultExpandAll={!isEmpty(searchText)}
                                    />
                                </div>
                                <Blocker isEnabled={isLoading} />
                            </Fragment>
                        );
                    }
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
