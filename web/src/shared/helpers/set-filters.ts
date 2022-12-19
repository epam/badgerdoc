import React from 'react';
import { Filter, Operators, TableFilters } from '../../api/typings';
import { DataSourceState } from '@epam/uui';

export function getFiltersSetter<T>(
    filtersState: Filter<keyof T>[],
    setFiltersState: React.Dispatch<React.SetStateAction<Filter<keyof T>[]>>
) {
    return (filtersToAdd: (Filter<keyof T> | null)[]) => {
        let resultFilters: Filter<keyof T>[] = [...filtersState];

        if (filtersToAdd.length === 0) {
            setFiltersState([]);
            return;
        }

        filtersToAdd.forEach((filter) => {
            if (!filter) {
                return;
            }
            const existedFilterIndex = resultFilters.findIndex(
                ({ field, operator }) => field === filter.field && operator === filter.operator
            );
            if (existedFilterIndex > -1) {
                if (filter.value) {
                    resultFilters[existedFilterIndex].value = filter.value;
                } else {
                    resultFilters.splice(existedFilterIndex);
                }
            } else {
                if (filter.value) {
                    resultFilters.push(filter);
                }
            }
        });
        setFiltersState(resultFilters);
    };
}

export function prepareFiltersToSet<TEntity, TFilters>(
    tableValue: DataSourceState<TableFilters<TEntity, TFilters>, unknown>
) {
    const filters = Object.keys(tableValue.filter!);
    return filters.flatMap((item) => {
        const field = item as keyof TEntity;
        const filter = tableValue.filter![field as keyof TEntity];
        const operator = Object.keys(tableValue.filter![field as keyof TEntity]!)[0] as Operators;
        const operatorsArray = Object.keys(filter!);
        if (operatorsArray.length === 1) {
            return {
                field,
                operator: operatorsArray[0] as Operators,
                value: filter![operator]! as string[]
            };
        } else if ('from' in filter! && 'to' in filter) {
            return [
                { field, operator: Operators.GE, value: filter['from'] },
                { field, operator: Operators.LE, value: filter['to'] }
            ];
        } else {
            return null;
        }
    });
}

export function saveFiltersToStorage(filters: any, field: string) {
    const localFilters = JSON.parse(sessionStorage.getItem('filters') || '{}');
    localFilters[field] = filters;
    sessionStorage.setItem('filters', JSON.stringify(localFilters));
}

export function getFiltersFromStorage(field: string) {
    const localString = sessionStorage.getItem('filters');
    if (localString) {
        const localFilters = JSON.parse(localString);
        return localFilters[field];
    }
    return null;
}

export function clearFiltersFromStorage() {
    sessionStorage.removeItem('filters');
}
