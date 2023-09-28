// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useCallback, useEffect, useState } from 'react';

import { Category, CategoryNode } from 'api/typings';
import { BadgerTree } from 'shared/components/badger-tree/badger-tree';

import styles from './categories-tree.module.scss';

interface CategoriesTreeProps {
    categoriesHeight: number;
    categoryNodes: CategoryNode[];
    isLoading: boolean;
    selectedCategory?: Category;
    onCategorySelected: (category: Category) => void;
    selectedHotKeys: string[];
}

const itemHeight = 33;

export const CategoriesTree: FC<CategoriesTreeProps> = ({
    categoriesHeight,
    isLoading,
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
            isLoading={isLoading}
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
