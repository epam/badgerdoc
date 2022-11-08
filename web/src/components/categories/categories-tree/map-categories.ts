import { Category, CategoryNode } from 'api/typings';
import { isEmpty } from 'lodash';

export const mapCategory = (category: Category, hotKey?: string): CategoryNode => ({
    key: category.id,
    title: category.name,
    isLeaf: isEmpty(category.children),
    children: [],
    category,
    hotKey
});

export const mapCategories = (categories?: Category[]): CategoryNode[] => {
    if (!categories) {
        return [];
    }
    const nodeById = new Map<string, CategoryNode>();
    const rootNodes = [];

    const setNode = (category: Category) => {
        const categoryNode = mapCategory(category);
        if (!nodeById.has(category.id)) {
            nodeById.set(category.id, categoryNode);
        }
    };

    for (const category of categories) {
        setNode(category);
        if (category.parents?.length) {
            for (let parentCategory of category.parents) {
                setNode(parentCategory);
            }
        }
    }
    for (let [, value] of nodeById) {
        if (!value.category.parent) {
            rootNodes.push(value);
        }
        if (value.category.children) {
            for (let childId of value.category.children) {
                const child = nodeById.get(childId);
                if (child) value.children.push(child);
            }
        }
    }

    return rootNodes;
};
