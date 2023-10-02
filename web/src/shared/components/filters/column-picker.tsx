// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { ReactNode, useCallback, useMemo } from 'react';
import { ColumnPickerFilter, RangeDatePicker } from '@epam/loveship';
import { IDataSource, ILens } from '@epam/uui';
import { Operators } from 'api/typings';

const isStringItem = (item: string | unknown): item is string => {
    return typeof item === 'string';
};

const isBooleanItem = (item: boolean | unknown): item is boolean => {
    return typeof item === 'boolean';
};

export const useDateRangeFilter = (filterId: string) => {
    return useCallback(
        (filterLens: ILens<any>): ReactNode => (
            <RangeDatePicker {...filterLens.prop(filterId).toProps()} />
        ),
        []
    );
};

export const useColumnPickerFilter = <TItem, TId, TFilter, TProperty extends string>(
    dataSource: IDataSource<TItem, TId, TFilter>,
    field: TProperty,
    options: {
        isPickByEntity?: boolean;
        getName?: (item: TItem | boolean) => string;
        showSearch: boolean;
    } = { isPickByEntity: true, showSearch: false }
) => {
    const getItemName = useCallback((item: string | TItem | boolean) => {
        if (isStringItem(item)) {
            return item;
        } else if (isBooleanItem(item)) {
            if (options.getName) return options.getName(item);
            return item.toString();
        } else {
            if (!options.getName) {
                throw new Error('getName argument should be provided');
            }
            return options.getName(item);
        }
    }, []);

    const handleRenderColumnPickerFilter = useCallback(
        (filterLens: ILens<Record<TProperty, { [Operators.IN]: Array<TItem> }>>): ReactNode => (
            <ColumnPickerFilter<TItem, TId>
                dataSource={dataSource}
                selectionMode="multi"
                valueType="entity"
                emptyValue={null}
                getName={getItemName}
                showSearch={options.showSearch}
                {...filterLens.prop(field).prop(Operators.IN).toProps()}
            />
        ),
        []
    );

    const handleRenderColumnPickerFilterById = useCallback(
        (filterLens: ILens<Record<TProperty, { [Operators.IN]: Array<TId> }>>): ReactNode => (
            <ColumnPickerFilter<TItem, TId>
                dataSource={dataSource}
                selectionMode="multi"
                valueType="id"
                emptyValue={null}
                getName={getItemName}
                showSearch={options.showSearch}
                {...filterLens.prop(field).prop(Operators.IN).toProps()}
            />
        ),
        []
    );

    return useMemo(
        () =>
            options.isPickByEntity
                ? handleRenderColumnPickerFilter
                : handleRenderColumnPickerFilterById,
        [options.isPickByEntity]
    );
};
