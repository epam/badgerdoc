import { getFiltersSetter } from '../set-filters';
import { FilterWithDocumentExtraOption, Operators } from '../../../api/typings';

describe('TableHook filters setter', () => {
    type TestJob = {
        name: string;
        type: string;
    };

    const setFiltersStateMock = jest.fn();

    test('should add filter to list if filter passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'type',
                operator: Operators.IN,
                value: ['type_1']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'type',
                operator: Operators.IN,
                value: ['type_1']
            }
        ]);
    });

    test('should set new value list if filter with the same name was passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['name 1']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['name 1', 'name 2']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'name',
                operator: Operators.IN,
                value: ['name 1', 'name 2']
            }
        ]);
    });

    test('should add new filter to list if new filter passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'type',
                operator: Operators.IN,
                value: ['type_1']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['type_1']
            }
        ]);
    });

    test('should remove filter from list (and this way have empty filter) if empty value was passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([]);
    });

    test('should remove filter from list (and keep filter with other name) if empty value was passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type']
            }
        ]);
    });

    test('should remove all filters from list which were passed with empty values', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN
            },
            {
                field: 'type',
                operator: Operators.IN
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([]);
    });

    test('should set new value if filter with the same name was passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['new test name']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'name',
                operator: Operators.IN,
                value: ['new test name']
            }
        ]);
    });

    test('should set new value list for each filter if several filters with new values were passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 1']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type 1', 'test type 2']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 2']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type 3', 'test type 4']
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 2']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type 3', 'test type 4']
            }
        ]);
    });

    test('should remove one value and replace another when two filters (with new and absent values respectively) were passed as argument', () => {
        const filtersState: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 1']
            },
            {
                field: 'type',
                operator: Operators.IN,
                value: ['test type']
            }
        ];

        const filtersToSet: FilterWithDocumentExtraOption<keyof TestJob>[] = [
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 2']
            },
            {
                field: 'type',
                operator: Operators.IN
            }
        ];

        const setFilters = getFiltersSetter<TestJob>(filtersState, setFiltersStateMock);
        setFilters(filtersToSet);

        expect(setFiltersStateMock).toHaveBeenCalledWith([
            {
                field: 'name',
                operator: Operators.IN,
                value: ['test name 2']
            }
        ]);
    });
});
