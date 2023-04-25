import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { useCategoriesTree } from '../categories-tree/use-categories-tree';
import { AnnotationBoundMode } from 'shared';
import { CategoriesTree } from 'components/categories/categories-tree/categories-tree';
import { Category, CategoryNode } from '../../../api/typings';

import { Blocker, FlexCell, MultiSwitch, SearchInput } from '@epam/loveship';
import styles from './categories-tab.module.scss';

interface CategoriesTabProps {
    boundModeSwitch: AnnotationBoundMode;
    setBoundModeSwitch: (type: AnnotationBoundMode) => void;
}

const getSubItems = (categories: Category[]): any[] => {
    const tabs = [];
    if (categories.some((el) => el.type === 'box'))
        tabs.push({
            id: 'box',
            caption: 'Layout',
            cx: styles.categoriesAndLinks
        });
    if (categories.some((el) => el.type === 'link'))
        tabs.push({
            id: 'link',
            caption: 'Links',
            cx: styles.categoriesAndLinks
        });
    if (categories.some((el) => el.type === 'segmentation'))
        tabs.push({
            id: 'segmentation',
            caption: 'Segmentation',
            cx: styles.categoriesAndLinks
        });

    return tabs;
};

export const CategoriesTab = ({ boundModeSwitch, setBoundModeSwitch }: CategoriesTabProps) => {
    const { categories: taskCategories, onCategorySelected, getJobId } = useTaskAnnotatorContext();

    const [searchText, setSearchText] = useState('');
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

    const treeContainerRef = useRef<HTMLDivElement>(null);

    const { categoryNodes, isFetched } = useCategoriesTree({
        searchText,
        boundModeSwitch,
        jobId: getJobId()
    });

    const addHotKey = (categoryNodes: CategoryNode[]) => {
        const hotKeys = '123456789qwertyuiopasdfghjklzxcvbnm';

        const hotKeysMap = new Map<string, CategoryNode>();
        let index = 0;
        const mapHotKeys = (categoryNodes: CategoryNode[]) => {
            for (let value of categoryNodes) {
                value.hotKey = hotKeys[index++];
                hotKeysMap.set(value.hotKey, value);
                if (value.children) {
                    mapHotKeys(value.children);
                }
            }
        };
        mapHotKeys(categoryNodes);
        return hotKeysMap;
    };

    useEffect(() => {
        if (!categoryNodes?.length) {
            return;
        }
        const hotKeysMap = addHotKey(categoryNodes);

        const handleKey = (event: KeyboardEvent) => {
            const keyCode = event.key;
            const selectedNode = hotKeysMap.get(keyCode);
            if (selectedNode && selectedNode.category) {
                onCategorySelected(selectedNode.category);
                setSelectedKeys([selectedNode.key]);
            }
        };

        document.addEventListener('keydown', handleKey);
        return () => {
            document.removeEventListener('keydown', handleKey);
        };
    }, [categoryNodes]);

    const categoriesTypes = useMemo(() => {
        return !taskCategories ? [] : getSubItems(taskCategories);
    }, [taskCategories]);

    const treeHeight = treeContainerRef.current?.getBoundingClientRect().height || 0;

    return (
        <div className={styles.container}>
            {categoriesTypes.length > 1 && (
                <FlexCell width="auto" cx={styles.categoriesAndLinks__wrapper}>
                    <MultiSwitch
                        size="30"
                        items={categoriesTypes}
                        value={boundModeSwitch}
                        onValueChange={setBoundModeSwitch}
                    />
                </FlexCell>
            )}
            {categoryNodes?.length > 20 && (
                <SearchInput
                    value={searchText}
                    debounceDelay={300}
                    cx={styles.search}
                    onValueChange={(text = '') => setSearchText(text)}
                />
            )}
            <div className={styles.categories} ref={treeContainerRef}>
                <CategoriesTree
                    key={searchText}
                    categoriesHeight={treeHeight}
                    isLoading={!isFetched}
                    categoryNodes={categoryNodes}
                    onCategorySelected={onCategorySelected}
                    selectedHotKeys={selectedKeys}
                />
            </div>
            <Blocker isEnabled={!isFetched} />
        </div>
    );
};
