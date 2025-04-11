// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { noop } from 'lodash';
import { FacetFilter } from 'api/typings/search';
import { DocumentView, FileDocument } from 'api/typings';
import { Breadcrumbs } from 'api/typings/documents';
import { SortingDirection } from 'api/typings';


type DocumentsSearchContext = {
    query: string;
    facetFilter: FacetFilter;
    documentView: DocumentView;
    breadcrumbs: Breadcrumbs[];
    documentsSort: string;
    documentsSortOrder: SortingDirection;
    setQuery: (query: string) => void;
    setFacetFilter: (facetFilter: any) => void;
    setDocumentView: (view: DocumentView) => void;
    setDocumentsSort: (view: DocumentView) => void;
    toggleSortOrder: () => void;
};

const defaultFacetFilters = {
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
    documentsSortOrder: SortingDirection.ASC,
    setQuery: noop,
    setFacetFilter: noop,
    setDocumentView: noop,
    setDocumentsSort: noop,
    toggleSortOrder: noop
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
    const [sortOrder, setSortOrder] = useState<SortingDirection>(
        'asc' as SortingDirection
    );

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
        setSortOrder(prev => {
            if (prev === SortingDirection.ASC) return SortingDirection.DESC;
            return SortingDirection.ASC;
        })
    }

    useEffect(() => {
        if (isDocuments) {
            setBreadcrumbs(documentsBreadcrumbs);
            setDocumentsSort('last_modified');
            setSortOrder(SortingDirection.ASC)
            setQuery('');
        }
        if (isSearch) {
            setBreadcrumbs(searchBreadcrumbs);
            setDocumentsSort('relevancy');
            setQuery('');
        }
    }, [history.location.pathname]);

    useEffect(() => {
        if (isSearch) pushSearchUrl();
    }, [query, documentsSort, facetFilter]);

    const value: DocumentsSearchContext = useMemo<DocumentsSearchContext>(() => {
        return {
            query,
            facetFilter,
            documentView,
            breadcrumbs,
            documentsSort,
            documentsSortOrder: sortOrder,
            setQuery,
            setFacetFilter,
            setDocumentView,
            setDocumentsSort,
            toggleSortOrder
        };
    }, [query, facetFilter, documentView, breadcrumbs, documentsSort, sortOrder]);
    return <DocumentsSearch.Provider value={value}>{children}</DocumentsSearch.Provider>;
};
