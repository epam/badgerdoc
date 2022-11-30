import { Category, CategoryNode } from 'api/typings';
import React, { FC, useCallback, useEffect, useState } from 'react';
import styles from './categories-tree.module.scss';
import { BadgerTree } from 'shared/components/tree/tree';

interface CategoriesTreeProps {
    categoriesHeight: number;
    categoryNodes: CategoryNode[];
    selectedCategory?: Category;
    onCategorySelected: (category: Category) => void;
    selectedHotKeys: string[];
}

const itemHeight = 32;

export const CategoriesTree: FC<CategoriesTreeProps> = ({
    categoriesHeight,
    categoryNodes,
    onCategorySelected,
    selectedHotKeys
}) => {
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

    useEffect(() => {
        if (selectedHotKeys) {
            setSelectedKeys(selectedHotKeys);
        }
    }, [selectedHotKeys]);

    const titleRenderer = useCallback((node: CategoryNode) => {
        const boxStyle = {
            border: `1px solid ${node?.category?.metadata?.color}`
        };
        return (
            <div
                style={{ color: node.category?.metadata?.color }}
                className={styles.categoryWrapper}
            >
                {node.hotKey && (
                    <div className={styles.hotkey} style={boxStyle}>
                        {node.hotKey.toUpperCase()}
                    </div>
                )}
                <div style={{ color: node.category?.metadata?.color }} className={styles.category}>
                    {node.title}
                </div>
            </div>
        );
    }, []);

    const handleSelect = useCallback(
        (selectedKeys, info) => {
            onCategorySelected(info.node.category);
            setSelectedKeys(selectedKeys);
        },
        [onCategorySelected]
    );

    return (
        <BadgerTree
            nodes={categoryNodes}
            height={categoriesHeight}
            itemHeight={itemHeight}
            titleRenderer={titleRenderer}
            onSelect={handleSelect}
            defaultExpandAll
            selectedKeys={selectedKeys}
        />
    );
};
