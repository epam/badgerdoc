import { Spinner } from '@epam/loveship';
import { TaxonomyNode, TreeNode } from 'api/typings';
import React, { FC, useCallback, useState } from 'react';
import styles from './taxonomies-tree.module.scss';
import { EventDataNode } from 'rc-tree/lib/interface';
import { BadgerTree } from 'shared/components/tree/tree';
import { Annotation, AnnotationLabel } from 'shared';

interface TaxonomiesTreeProps {
    taxonomiesHeight: number;
    taxonomyNodes: TaxonomyNode[];
    onLoadData: (treeNode: EventDataNode<TaxonomyNode>) => Promise<any>;
    expandNode?: string;
    selectedAnnotation?: Annotation;
    onAnnotationEdited: (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => void;
    currentPage: number;
    onDataAttributesChange: (elIndex: number, value: string) => void;
    elementIndex: number;
    selectedKey: string;
    defaultExpandAll: boolean;
}

const itemHeight = 32;

export const TaxonomiesTree: FC<TaxonomiesTreeProps> = ({
    taxonomiesHeight,
    taxonomyNodes,
    onLoadData,
    expandNode,
    selectedAnnotation,
    onAnnotationEdited,
    currentPage,
    onDataAttributesChange,
    elementIndex,
    selectedKey,
    defaultExpandAll
}) => {
    const [selectedKeys, setSelectedKeys] = useState<string[]>([selectedKey]);

    const titleRenderer = useCallback(
        (node: TreeNode) => {
            return (
                <div className={styles.taxonomyWrapper}>
                    <div className={styles.taxonomy}>{node.title}</div>
                    {expandNode === node.key && <Spinner color="sky" />}
                </div>
            );
        },
        [expandNode]
    );

    const handleSelect = useCallback((selectedKeys, info) => {
        setSelectedKeys(selectedKeys);
        if (selectedAnnotation?.labels) {
            const labelToChangeIdx: number = selectedAnnotation?.labels.findIndex(
                (label: AnnotationLabel) => label.annotationId === selectedAnnotation.id
            );

            const changedLabel: AnnotationLabel = {
                ...selectedAnnotation?.labels[labelToChangeIdx],
                label: info.node.title
            };

            selectedAnnotation.labels[labelToChangeIdx] = changedLabel;
        }
        onAnnotationEdited(currentPage, selectedAnnotation?.id!, { label: info.node.title });
        onDataAttributesChange(elementIndex, info.node.key);
    }, []);
    return (
        <BadgerTree
            nodes={taxonomyNodes}
            height={taxonomiesHeight}
            onLoadData={onLoadData}
            itemHeight={itemHeight}
            titleRenderer={titleRenderer}
            onSelect={handleSelect}
            selectedKeys={selectedKeys}
            defaultExpandAll={defaultExpandAll}
        />
    );
};
