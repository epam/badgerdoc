import { useCategories, categoriesFetcher } from 'api/hooks/categories';
import { CategoryNode, Operators, SortingDirection, Category, Filter } from 'api/typings';
import { isEmpty } from 'lodash';
import { useMemo, useState, useEffect } from 'react';
import { AnnotationBoundMode } from 'shared';
import { mapCategories, mapCategory } from './map-categories';

interface Props {
    searchText: string;
    boundModeSwitch: AnnotationBoundMode;
    isTaskCategoriesTree?: boolean;
    taskCategories?: Category[];
}

export const useCategoriesTree = ({
    searchText,
    boundModeSwitch,
    isTaskCategoriesTree,
    taskCategories
}: Props) => {
    const [categoryNodes, setCategoryNodes] = useState<CategoryNode[]>([]);
    const [expandNode, setExpandNode] = useState<string>();

    const boundModeFilter: Filter<keyof Category> = useMemo(
        () => ({
            field: 'type',
            operator: Operators.EQ,
            value: boundModeSwitch
        }),
        [boundModeSwitch]
    );
    const { data: rootCategories, refetch: refetchRoot } = useCategories(
        {
            page: 1,
            size: 100,
            searchText: '',
            filters: [
                {
                    field: 'parent',
                    operator: Operators.IS_NULL
                },
                boundModeFilter
            ],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );
    const searchFilters: Filter<keyof Category>[] = useMemo(() => {
        const filters: Filter<keyof Category>[] = [];
        if (isTaskCategoriesTree) {
            filters.push({
                field: 'id',
                operator: Operators.IN,
                value: taskCategories?.map((category) => category.id)
            });
        }
        if (boundModeSwitch) {
            filters.push(boundModeFilter);
        }
        return filters;
    }, [isTaskCategoriesTree, boundModeSwitch]);

    const searchResult = useCategories(
        {
            page: 1,
            size: 100,
            searchText,
            filters: searchFilters,
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false, cacheTime: 0 }
    );

    useEffect(() => {
        if (isTaskCategoriesTree === false) {
            refetchRoot();
        }
    }, [isTaskCategoriesTree, taskCategories, boundModeSwitch]);

    useEffect(() => {
        if (searchText) {
            searchResult.refetch();
        }
    }, [searchText, boundModeSwitch]);

    useEffect(() => {
        if (searchText) {
            if (searchResult.data?.data) {
                setCategoryNodes(mapCategories(searchResult.data?.data));
            } else {
                setCategoryNodes([]);
            }
        } else if (isTaskCategoriesTree) {
            setCategoryNodes(
                mapCategories(
                    taskCategories?.filter((category) => category.type === boundModeSwitch)
                )
            );
        } else {
            setCategoryNodes(mapCategories(rootCategories?.data));
        }
    }, [
        taskCategories,
        rootCategories,
        searchResult.data,
        searchText,
        isTaskCategoriesTree,
        boundModeSwitch
    ]);

    const updateTreeData = (
        list: CategoryNode[],
        key: string,
        children: CategoryNode[]
    ): CategoryNode[] =>
        list.map((node) => {
            if (node.key === key) {
                return {
                    ...node,
                    children
                };
            }
            if (node.children && !isEmpty(node.children)) {
                return {
                    ...node,
                    children: updateTreeData(node.children, key, children)
                };
            }
            return node;
        });

    const onLoadData = async (node: CategoryNode) => {
        if (!isEmpty(node.children)) {
            return node.children;
        }
        setExpandNode(node.key);
        const parentFilter: Filter<keyof Category> = {
            field: 'parent',
            operator: Operators.EQ,
            value: node.key
        };
        const childCategories = await categoriesFetcher(1, 100, '', [
            parentFilter,
            boundModeFilter
        ]);

        if (childCategories) {
            setExpandNode(undefined);

            const childNodes = childCategories.data.map((category) => mapCategory(category));
            setCategoryNodes((prevState) => updateTreeData(prevState, node.key, childNodes));
        }
        return node.children;
    };

    return { categoryNodes, onLoadData, expandNode };
};
