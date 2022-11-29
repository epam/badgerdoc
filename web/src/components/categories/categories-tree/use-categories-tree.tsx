import { useCategoriesByJob } from 'api/hooks/categories';
import { CategoryNode, Operators, SortingDirection, Category, Filter } from 'api/typings';
import { useMemo, useState, useEffect } from 'react';
import { AnnotationBoundMode } from 'shared';
import { mapCategories } from './map-categories';

interface Props {
    searchText: string;
    boundModeSwitch: AnnotationBoundMode;
    jobId?: number;
}

export const useCategoriesTree = ({ searchText, boundModeSwitch, jobId }: Props) => {
    const [categoryNodes, setCategoryNodes] = useState<CategoryNode[]>([]);

    const boundModeFilter: Filter<keyof Category> = useMemo(
        () => ({
            field: 'type',
            operator: Operators.EQ,
            value: boundModeSwitch
        }),
        [boundModeSwitch]
    );

    const searchFilters: Filter<keyof Category>[] = useMemo(() => {
        const filters: Filter<keyof Category>[] = [];

        if (boundModeSwitch) {
            filters.push(boundModeFilter);
        }
        return filters;
    }, [boundModeSwitch]);

    const searchResult = useCategoriesByJob(
        {
            jobId,
            page: 1,
            size: 100,
            searchText,
            filters: searchFilters,
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );

    useEffect(() => {
        if (jobId) {
            searchResult.refetch();
        }
    }, [searchText, boundModeSwitch, jobId]);

    useEffect(() => {
        if (jobId) setCategoryNodes(mapCategories(searchResult.data?.data));
    }, [searchResult.data, searchText, boundModeSwitch]);

    return { categoryNodes };
};
