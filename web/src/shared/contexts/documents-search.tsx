// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { FileDocument, SortingDirection } from '../../api/typings';
import { noop } from 'lodash';
import { SelectedFilesProvider } from './SelectedFilesContext';

type DocumentView = 'card' | 'table';
type Breadcrumbs = { name: string; url: string };
type FacetFilter = {
    category: Array<{ id: string; value: boolean }>;
    job_id: Array<{ id: string; value: boolean }>;
};
type FacetName = keyof FacetFilter;
type FacetValuesFilter = Array<{ id: string; value: boolean }>;

type DocumentsSearchContext = {
    query: string;
    facetFilter: FacetFilter;
    documentView: DocumentView;
    breadcrumbs: Breadcrumbs[];
    documentsSort: string;
    documentsSortOrder: SortingDirection;
    selectedFiles: number[];
    setQuery: (query: string) => void;
    setFacetFilter: (facetFilter: FacetFilter) => void;
    setDocumentView: (view: DocumentView) => void;
    setDocumentsSort: (sort: string) => void;
    toggleSortOrder: () => void;
    onFacetFilterChange: (name: FacetName, filterValue: FacetValuesFilter) => void;
    onValueChange: (name: FacetName, id: string) => void;
};

const defaultFacetFilters: FacetFilter = {
    category: [],
    job_id: []
};

const documentsBreadcrumbs: Breadcrumbs[] = [
    {
        name: 'Documents',
        url: '/documents'
    }
];

const searchBreadcrumbs: Breadcrumbs[] = [
    ...documentsBreadcrumbs,
    {
        name: 'Search',
        url: '/documents/search'
    }
];

export const DocumentsSearch = React.createContext<DocumentsSearchContext>({
    query: '',
    facetFilter: defaultFacetFilters,
    documentView: 'card',
    breadcrumbs: [],
    documentsSort: '',
    selectedFiles: [],
    documentsSortOrder: SortingDirection.ASC,
    setQuery: noop,
    setFacetFilter: noop,
    setDocumentView: noop,
    setDocumentsSort: noop,
    toggleSortOrder: noop,
    onFacetFilterChange: noop,
    onValueChange: noop
});

export const DocumentsSearchProvider: FC = ({ children }) => {
    const history = useHistory();
    const [query, setQuery] = useState<string>('');
    const [facetFilter, setFacetFilter] = useState<FacetFilter>(defaultFacetFilters);
    const [documentView, setDocumentView] = useState<DocumentView>('card');
    const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumbs[]>([]);
    const [documentsSort, setDocumentsSort] = useState<string | keyof FileDocument>(
        'last_modified'
    );
    const [sortOrder, setSortOrder] = useState<SortingDirection>(SortingDirection.ASC);

    const onValueChange = (name: FacetName, id: string) => {
        setFacetFilter((prevState: FacetFilter) => ({
            ...prevState,
            [name]: prevState[name].map((item) =>
                item.id === id ? { ...item, value: !item.value } : item
            )
        }));
    };

    const onFacetFilterChange = (name: FacetName, filterValue: FacetValuesFilter) => {
        setFacetFilter((prevState: FacetFilter) => ({
            ...prevState,
            [name]: filterValue
        }));
    };

    const [selectedFiles, setSelectedFiles] = useState<number[]>([]);
    const isDocuments = history.location.pathname === '/documents';
    const isSearch = history.location.pathname === '/documents/search';

    const pushSearchUrl = () => {
        let url = '';
        const job: string[] = [];
        const category: string[] = [];

        Object.values(facetFilter.job_id).forEach(({ id, value }) => value && job.push(id));
        Object.values(facetFilter.category).forEach(({ id, value }) => value && category.push(id));

        if (query.length) {
            url = url + `query=${query}`;
        } else {
            url = url.split('query=').join();
        }

        if (documentsSort.length && documentsSort !== 'relevancy') {
            url = url + `sort=${documentsSort}`;
        }

        if (job.length) {
            url = url + `jobs=${job.slice()}`;
        }

        if (category.length) {
            url = url + `category=${category.slice()}`;
        }

        history.push({ search: url });
    };

    const toggleSortOrder = () => {
        setSortOrder((prev) =>
            prev === SortingDirection.ASC ? SortingDirection.DESC : SortingDirection.ASC
        );
    };

    useEffect(() => {
        if (isDocuments) {
            setBreadcrumbs(documentsBreadcrumbs);
            setDocumentsSort('last_modified');
            setSortOrder(SortingDirection.ASC);
            setQuery('');
            setSelectedFiles([]);
        }
        if (isSearch) {
            setBreadcrumbs(searchBreadcrumbs);
            setDocumentsSort('relevancy');
            setQuery('');
            setSelectedFiles([]);
        }
    }, [history.location.pathname]);

    useEffect(() => {
        if (isSearch) pushSearchUrl();
    }, [query, documentsSort, facetFilter]);

    const value: DocumentsSearchContext = useMemo(
        () => ({
            query,
            facetFilter,
            documentView,
            breadcrumbs,
            documentsSort,
            documentsSortOrder: sortOrder,
            selectedFiles,
            setQuery,
            setFacetFilter,
            setDocumentView,
            setDocumentsSort,
            toggleSortOrder,
            onFacetFilterChange,
            onValueChange
        }),
        [query, facetFilter, documentView, breadcrumbs, documentsSort, sortOrder]
    );

    return (
        <DocumentsSearch.Provider value={value}>
            <SelectedFilesProvider>{children}</SelectedFilesProvider>
        </DocumentsSearch.Provider>
    );
};
