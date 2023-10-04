// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import { useCategoriesByJob } from 'api/hooks/categories';
import {
    CategoryNode,
    Operators,
    SortingDirection,
    Category,
    FilterWithDocumentExtraOption
} from 'api/typings';
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

    const boundModeFilter: FilterWithDocumentExtraOption<keyof Category> = useMemo(
        () => ({
            field: 'type',
            operator: Operators.EQ,
            value: boundModeSwitch
        }),
        [boundModeSwitch]
    );

    const searchFilters: FilterWithDocumentExtraOption<keyof Category>[] = useMemo(() => {
        const filters: FilterWithDocumentExtraOption<keyof Category>[] = [];

        if (boundModeSwitch) {
            filters.push(boundModeFilter);
        }
        return filters;
    }, [boundModeSwitch]);

    const {
        data: { pages: searchResult } = {},
        isFetching,
        refetch
    } = useCategoriesByJob(
        {
            jobId,
            size: 100,
            searchText,
            filters: searchFilters,
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );

    useEffect(() => {
        if (jobId) {
            refetch();
        }
    }, [searchText, boundModeSwitch, jobId]);

    useEffect(() => {
        if (jobId) setCategoryNodes(mapCategories(searchResult));
    }, [searchResult, searchText, boundModeSwitch]);

    return { categoryNodes, isFetching };
};
