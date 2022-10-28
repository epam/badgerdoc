import { useMemo } from 'react';
import { DataColumnProps } from '@epam/uui';

type Filter = {
    key: string;
    render: any;
};

export const useTableColumns = (columns: DataColumnProps<any>[], filters: Filter[]) => {
    return useMemo(() => {
        filters.forEach((el) => {
            const filterColumn = columns.find(({ key }) => key === el.key);
            filterColumn!.isFilterActive = (filter) =>
                (filter[el.key] && filter[el.key].in && !!filter[el.key].in.length) ?? false;
            filterColumn!.renderFilter = el.render;
        });
        return columns;
    }, []);
};
