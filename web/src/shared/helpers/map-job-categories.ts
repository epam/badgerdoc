import { Category, PagedResponse } from '../../api/typings';

export const mapDocumentCategories = (categories: PagedResponse<Category>) => {
    if (Array.isArray(categories?.data)) {
        return categories.data.reduce((acc, item) => {
            if (!acc.has(item.id)) {
                acc.set(item.id, { color: item.metadata && item.metadata.color, label: item.name });
            }
            return acc;
        }, new Map());
    } else return new Map();
};
