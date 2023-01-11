import { Category } from '../../api/typings';
import { Text } from '@epam/loveship';
import React from 'react';
import { DataColumnProps } from '@epam/uui';

export const categoryColumns: DataColumnProps<Category>[] = [
    {
        key: 'id',
        caption: 'id',
        render: (categories: Category) => {
            return <Text key={categories.id}> {categories.id} </Text>;
        },
        isSortable: true,
        grow: 2,
        shrink: 1,
        width: 100
    },
    {
        key: 'name',
        caption: 'Categories name',
        render: (categories: Category) => {
            return (
                <Text key={categories.id}>
                    <div style={{ color: categories?.metadata?.color }}>{categories.name}</div>
                </Text>
            );
        },
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'parent',
        caption: 'Parent id',
        render: (categories: Category) => {
            return <Text key={categories.id}> {String(categories.parent)}</Text>;
        },
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'type',
        caption: 'Type',
        render: (categories: Category) => {
            return <Text key={categories.id}> {String(categories.type)} </Text>;
        },
        isSortable: false,
        grow: 1,
        shrink: 1,
        width: 100
    }
];
