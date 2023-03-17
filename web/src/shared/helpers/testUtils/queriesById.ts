import {
    queryHelpers,
    buildQueries,
    Matcher,
    MatcherOptions,
    GetErrorFunction
} from '@testing-library/react';

const queryAllById = (container: HTMLElement, id: Matcher, options?: MatcherOptions | undefined) =>
    queryHelpers.queryAllByAttribute('id', container, id, options);

const getMultipleError: GetErrorFunction = (_, id) =>
    `Found multiple elements with the id attribute of: ${id}`;
const getMissingError: GetErrorFunction = (_, id) =>
    `Unable to find an element with the id attribute of: ${id}`;

const [queryById, getAllById, getById, findAllById, findById] = buildQueries(
    queryAllById,
    getMultipleError,
    getMissingError
);

export { queryAllById, queryById, getAllById, getById, findAllById, findById };
