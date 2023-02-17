import React, { FC, useCallback, useMemo } from 'react';
import { Spinner } from '@epam/loveship';
import { TaxonomyNode, TreeNode } from 'api/typings';
import { EventDataNode } from 'rc-tree/lib/interface';
import { BadgerTree } from 'shared/components/badger-tree/badger-tree';
import { Annotation, AnnotationLabel } from 'shared';
import styles from './taxonomies-tree.module.scss';

interface TaxonomiesTreeProps {
    isLoading: boolean;
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

const itemHeight = 33;

export const TaxonomiesTree: FC<TaxonomiesTreeProps> = ({
    isLoading,
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
    let selectedKeys = useMemo(() => {
        return [selectedKey];
    }, [selectedKey]);

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

    const handleSelect = useCallback(
        (pickedKeys, info) => {
            selectedKeys = pickedKeys;
            if (selectedAnnotation?.labels) {
                const labelToChangeIdx: number = selectedAnnotation?.labels.findIndex(
                    (label: AnnotationLabel) => label.annotationId === selectedAnnotation.id
                );

                const changedLabel: AnnotationLabel = {
                    ...selectedAnnotation?.labels[labelToChangeIdx],
                    label: info.node.taxon.name
                };

                selectedAnnotation.labels[labelToChangeIdx] = changedLabel;
            }
            onAnnotationEdited(currentPage, selectedAnnotation?.id!, {
                label: info.node.taxon.name
            });
            onDataAttributesChange(elementIndex, info.node.key);
        },
        [selectedKeys]
    );

    return (
        <BadgerTree
            isLoading={isLoading}
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
