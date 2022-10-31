import { useMemo, useRef } from 'react';
import { TableFilters } from 'api/typings';

export const useFiltersTable = <TItem>() => {
    const filters = useRef<TableFilters<TItem>>();

    return useMemo(() => filters, []);
};
