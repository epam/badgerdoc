import { BaseCategory, Category, CategoryNode } from 'api/typings';

export const mapCategory = (category: BaseCategory, hotKey?: string): CategoryNode => ({
    key: category.id,
    title: category.name,
    isLeaf: category.isLeaf,
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

    const setNode = (category: BaseCategory) => {
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
        if (!value.category?.parent) {
            rootNodes.push(value);
        } else {
            const parent = nodeById.get(value.category.parent);
            if (parent) {
                parent.children.push(value);
                parent.isLeaf = false;
            }
        }
    }

    return rootNodes;
};
