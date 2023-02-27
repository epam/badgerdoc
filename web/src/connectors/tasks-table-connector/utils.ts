import { Filter, TableFilters } from 'api/typings';
import { Task, TaskStatus } from 'api/typings/tasks';

export const getTableFilter = (localFilter: Filter<keyof Task>[]) =>
    localFilter.reduce(
        (accumulator: TableFilters<Task, boolean[] | TaskStatus[]>, { field, operator, value }) => {
            accumulator[field] = { [operator]: value };
            return accumulator;
        },
        {}
    );
