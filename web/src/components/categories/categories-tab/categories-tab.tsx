import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useHeight } from 'shared/hooks/use-height';
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
    if (!categories) return [];
    const res = [];
    if (categories.find((el) => el.type === 'box'))
        res.push({
            id: 'box',
            caption: 'Layout',
            cx: `${styles.categoriesAndLinks}`
        });
    if (categories.find((el) => el.type === 'link'))
        res.push({
            id: 'link',
            caption: 'Links',
            cx: `${styles.categoriesAndLinks}`
        });
    if (categories.find((el) => el.type === 'segmentation'))
        res.push({
            id: 'segmentation',
            caption: 'Segmentation',
            cx: `${styles.categoriesAndLinks}`
        });
    return res;
};

export const CategoriesTab = ({ boundModeSwitch, setBoundModeSwitch }: CategoriesTabProps) => {
    const { categories: taskCategories, onCategorySelected, getJobId } = useTaskAnnotatorContext();

    const [searchText, setSearchText] = useState('');
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

    const hightRef = useRef<HTMLDivElement>(null);
    const categoriesHeight = useHeight({ ref: hightRef });

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

    const { categoryNodes, isFetched } = useCategoriesTree({
        searchText,
        boundModeSwitch,
        jobId: getJobId()
    });

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
        if (taskCategories) {
            return getSubItems(taskCategories);
        }
        return [];
    }, [taskCategories]);

    return (
        <div className={styles.container}>
            {categoriesTypes.length > 1 && (
                <FlexCell width="auto" cx={styles.categoriesAndLinks__wrapper}>
                    <MultiSwitch
                        items={categoriesTypes}
                        value={boundModeSwitch}
                        onValueChange={
                            setBoundModeSwitch as React.Dispatch<React.SetStateAction<string>>
                        }
                    />
                </FlexCell>
            )}
            {categoryNodes?.length > 20 && (
                <SearchInput
                    value={searchText}
                    onValueChange={(text) => setSearchText(text ? text : '')}
                    debounceDelay={300}
                    cx={styles.search}
                />
            )}
            <div className={styles.categories} ref={hightRef}>
                <CategoriesTree
                    key={searchText}
                    categoriesHeight={categoriesHeight}
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
