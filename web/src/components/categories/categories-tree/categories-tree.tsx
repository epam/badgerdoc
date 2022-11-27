import { Spinner } from '@epam/loveship';
import { Category, CategoryNode } from 'api/typings';
import Tree from 'rc-tree';
import React, { FC, useCallback, useEffect, useState } from 'react';
import './rc-tree.scss';
import styles from './categories-tree.module.scss';
import { EventDataNode } from 'rc-tree/lib/interface';
import classNames from 'classnames';

interface CategoriesTreeProps {
    categoriesHeight: number;
    categoryNodes: CategoryNode[];
    onLoadData: (treeNode: EventDataNode<CategoryNode>) => Promise<any>;
    expandNode?: string;
    defaultExpand: boolean;
    selectedCategory?: Category;
    onCategorySelected: (category: Category) => void;
    selectedHotKeys: string[];
}

const itemHeight = 24;

export const CategoriesTree: FC<CategoriesTreeProps> = ({
    categoriesHeight,
    categoryNodes,
    onLoadData,
    expandNode,
    defaultExpand,
    selectedCategory,
    onCategorySelected,
    selectedHotKeys
}) => {
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

    useEffect(() => {
        if (selectedHotKeys) {
            setSelectedKeys(selectedHotKeys);
        }
    }, [selectedHotKeys]);

    const titleRenderer = useCallback(
        (node: CategoryNode) => {
            const boxStyle = {
                border: `1px solid ${node.category.metadata?.color}`
            };
            const selectedStyle =
                node.category.id === selectedCategory?.id ? 'rc-tree-treenode-selected' : '';
            return (
                <div
                    style={{ color: node.category.metadata?.color }}
                    className={styles.categoryWrapper}
                >
                    {node.hotKey && (
                        <div className={styles.hotkey} style={boxStyle}>
                            {node.hotKey.toUpperCase()}
                        </div>
                    )}
                    <div
                        style={{ color: node.category.metadata?.color }}
                        className={styles.category}
                    >
                        {node.title}
                    </div>
                    {expandNode === node.key && <Spinner color="sky" />}
                </div>
            );
        },
        [expandNode]
    );

    const handleSelect = useCallback(
        (selectedKeys, info) => {
            onCategorySelected(info.node.category);
            setSelectedKeys(selectedKeys);
        },
        [onCategorySelected]
    );

    return (
        <div className="animation">
            <div style={{ display: 'flex' }}>
                <div style={{ flex: '1 1 50%' }}>
                    {categoryNodes.length ? (
                        <Tree
                            treeData={categoryNodes}
                            loadData={onLoadData}
                            height={categoriesHeight}
                            itemHeight={itemHeight}
                            titleRender={titleRenderer}
                            onSelect={handleSelect}
                            selectedKeys={selectedKeys}
                            defaultExpandAll={defaultExpand}
                        ></Tree>
                    ) : (
                        <Spinner color="sky" />
                    )}
                </div>
            </div>
        </div>
    );
};
