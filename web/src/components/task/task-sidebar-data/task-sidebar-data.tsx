import React, { FC, Fragment, useMemo, useRef, useState } from 'react';
import { SearchInput, Text, TextArea } from '@epam/loveship';
import styles from './task-sidebar-data.module.scss';
import { CategoryDataAttributeWithValue } from 'api/typings';
import { TaxonomiesTree } from 'components/taxonomies/taxonomies-tree';
import { useTaxonomiesTree } from 'components/taxonomies/use-taxonomies-tree';
import { useHeight } from 'shared/hooks/use-height';
import { Annotation } from 'shared';
import { isEmpty } from 'lodash';

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
};

export const TaskSidebarData: FC<TaskSidebarDataProps> = ({
    annDataAttrs,
    selectedAnnotation,
    isCategoryDataEmpty,
    onDataAttributesChange,
    viewMode,
    onAnnotationEdited,
    currentPage
}) => {
    const [searchText, setSearchText] = useState('');

    const hightRef = useRef<HTMLDivElement>(null);
    const taxonomiesHeight = useHeight({ ref: hightRef });

    const dataAttrsArr =
        annDataAttrs && selectedAnnotation && annDataAttrs[+selectedAnnotation.id]
            ? annDataAttrs[+selectedAnnotation.id]
            : undefined;

    const taxonomyId = useMemo(() => {
        if (dataAttrsArr) {
            return dataAttrsArr.find((dataAttr) => dataAttr.type === 'taxonomy')?.name;
        }
    }, [dataAttrsArr]);

    const { taxonomyNodes, expandNode, onLoadData } = useTaxonomiesTree({
        searchText,
        taxonomyId
    });
    return (
        <div className={styles['task-sidebar-data']}>
            {isCategoryDataEmpty && (
                <Text>{`The selected category doesn't have data attributes`}</Text>
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
